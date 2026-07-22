"""
app/main.py
===========
FastAPI application factory for Project Atlas backend.

Startup sequence:
  1. Parse and validate all environment variables (fail fast if missing)
  2. Configure structured JSON logging
  3. Create FastAPI app with metadata
  4. Register exception handlers
  5. Register middleware (CORS, rate limiting, request logging)
  6. Mount the v1 API router
  7. Add /health and /ready probes for Railway deployment
  8. Connect to the database with retry on first request (lifespan handler)
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import AtlasBaseError
from app.core.rate_limiter import get_global_limit, limiter
from app.db.connection import check_db_health, close_db_connections, connect_with_retry

# ── Logging configuration ─────────────────────────────────────────────────────


def _configure_logging(log_level: str, environment: str) -> None:
    """
    Configure structlog for JSON output in production and
    coloured console output in development.
    """
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if environment == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Mirror standard library root logger level
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))


# ── Lifespan context manager ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.

    On startup: configure logging, verify DB connectivity with retry.
    On shutdown: drain and close all database connections.
    """
    cfg = get_settings()
    _configure_logging(cfg.LOG_LEVEL, cfg.ENVIRONMENT)
    logger = structlog.get_logger("app.startup")

    logger.info(
        "project_atlas.starting",
        version=cfg.APP_VERSION,
        environment=cfg.ENVIRONMENT,
    )

    # Verify DB connectivity (retries with exponential backoff)
    await connect_with_retry()
    logger.info("project_atlas.db_connected")

    yield  # ← Application runs here

    logger.info("project_atlas.shutting_down")
    await close_db_connections()
    logger.info("project_atlas.shutdown_complete")


# ── Application factory ───────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This is a factory function so the app can be created with different
    settings in tests (by patching environment variables before calling).
    """
    cfg = get_settings()

    app = FastAPI(
        title=cfg.APP_NAME,
        version=cfg.APP_VERSION,
        description=(
            "**Project Atlas** — Stochastic Supply Chain Stress-Testing System "
            "for the Nigerian Oil & Gas Sector.\n\n"
            "Runs 10,000-iteration Monte Carlo simulations to compute the "
            "probability distribution of disruption costs, delays, and supply "
            "chain failures under configurable scenarios.\n\n"
            "Target publication: International Journal of Production Economics (IJPE)."
        ),
        docs_url="/docs"     if cfg.DOCS_ENABLED else None,
        redoc_url="/redoc"   if cfg.DOCS_ENABLED else None,
        openapi_url="/openapi.json" if cfg.DOCS_ENABLED else None,
        lifespan=lifespan,
    )

    # ── Rate limiter state ────────────────────────────────────────────────────
    # SlowAPI requires the limiter to be stored on app.state
    app.state.limiter = limiter

    # ── Exception handlers ────────────────────────────────────────────────────
    _register_exception_handlers(app)

    # ── Middleware (order matters: first registered = outermost wrapper) ──────
    _register_middleware(app, cfg)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=cfg.API_V1_PREFIX)

    # ── Infrastructure probes ─────────────────────────────────────────────────
    _register_probes(app)

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers that convert exceptions to JSON."""

    @app.exception_handler(AtlasBaseError)
    async def atlas_error_handler(request: Request, exc: AtlasBaseError) -> JSONResponse:
        structlog.get_logger("app.exceptions").warning(
            "atlas_error",
            error_code=exc.error_code,
            message=exc.message,
            path=str(request.url.path),
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict(),
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down.",
                "retry_after": str(exc.retry_after) if hasattr(exc, "retry_after") else "60",
            },
            headers={"Retry-After": "60"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internal details in production
        cfg = get_settings()
        structlog.get_logger("app.exceptions").error(
            "unhandled_exception",
            error=str(exc),
            path=str(request.url.path),
            exc_info=True,
        )
        detail = str(exc) if not cfg.is_production else None
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected server error occurred.",
                **({"detail": detail} if detail else {}),
            },
        )


def _register_middleware(app: FastAPI, cfg) -> None:
    """Register middleware in correct order (outermost first)."""

    # 1. Request ID + structured request logging
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        structlog.get_logger("app.requests").info(
            "http_request",
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 1),
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(elapsed_ms, 1))
        return response

    # 2. SlowAPI rate limiting
    app.add_middleware(SlowAPIMiddleware)

    # 3. CORS — must be last registered (innermost), but most permissive scope
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
        max_age=3600,
    )


def _register_probes(app: FastAPI) -> None:
    """Add /health and /ready probes for Railway deployment and load balancers."""

    @app.get("/health", tags=["Infrastructure"], summary="Liveness probe")
    async def health() -> dict:
        """
        Returns 200 OK if the process is alive.
        Does NOT check DB connectivity (use /ready for that).
        Railway uses this to determine if the container should be restarted.
        """
        return {"status": "alive", "service": "project-atlas-backend"}

    @app.get("/ready", tags=["Infrastructure"], summary="Readiness probe")
    async def ready() -> dict:
        """
        Returns 200 OK if the application is ready to serve traffic.
        Checks database connectivity and returns pool statistics.
        Returns 503 if the database is unreachable.
        """
        db_health = await check_db_health()
        if db_health["status"] != "healthy":
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail={"status": "not_ready", "db": db_health},
            )
        return {
            "status": "ready",
            "db": db_health,
            "version": get_settings().APP_VERSION,
        }


# ── Module-level app instance (used by uvicorn and Railway) ──────────────────
app = create_app()
