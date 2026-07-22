"""
app/db/connection.py
====================
Async database connection layer built on SQLAlchemy 2.0 + asyncpg.

Design decisions:
- Single engine instance shared across the application lifetime.
- Async session factory yields sessions that are automatically closed
  on context exit, even if an exception occurs.
- Exponential backoff retry on initial connection (handles Railway cold start).
- Connection pool sized for Supabase free tier (max 60 direct connections;
  we use the transaction pooler which supports much higher concurrency).
- Health check exposed for Railway's health endpoint.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from tenacity import (
    RetryError,
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = structlog.get_logger(__name__)
_std_logger = logging.getLogger(__name__)

# ─── Module-level singletons ──────────────────────────────────────────────────
# Initialised once on first call to get_engine() and reused thereafter.
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine() -> AsyncEngine:
    """
    Create the SQLAlchemy async engine with connection pool settings.

    Pool configuration rationale for Supabase + Railway free tier:
        pool_size=5      — minimum persistent connections kept alive
        max_overflow=15  — burst connections above pool_size (total max = 20)
        pool_timeout=30  — seconds to wait for a connection from the pool
        pool_recycle=300 — recycle connections every 5 min to avoid server-side
                           idle timeouts (Supabase Transaction Pooler: 5 min)
        pool_pre_ping=True — validate connection before handing to application;
                             avoids "server closed the connection unexpectedly"
    """
    cfg = get_settings()
    engine = create_async_engine(
        cfg.DATABASE_URL,
        pool_size=cfg.DB_POOL_SIZE_MIN,
        max_overflow=cfg.DB_POOL_SIZE_MAX - cfg.DB_POOL_SIZE_MIN,
        pool_timeout=cfg.DB_POOL_TIMEOUT_SECONDS,
        pool_recycle=300,
        pool_pre_ping=True,
        echo=cfg.DB_ECHO_SQL,
        # asyncpg-specific connect_args
        connect_args={
            "server_settings": {
                "application_name": "project_atlas_backend",
                "jit": "off",           # disable JIT for short OLTP queries
            },
            "command_timeout": 60,      # per-statement timeout (seconds)
        },
        # Execution options applied to every statement
        execution_options={"isolation_level": "READ COMMITTED"},
    )
    _attach_engine_listeners(engine)
    return engine


def _attach_engine_listeners(engine: AsyncEngine) -> None:
    """Register SQLAlchemy engine-level event listeners for structured logging."""

    @event.listens_for(engine.sync_engine, "connect")
    def on_connect(dbapi_conn, connection_record):  # type: ignore[override]
        logger.debug("db.connection.acquired", pid=id(dbapi_conn))

    @event.listens_for(engine.sync_engine, "close")
    def on_close(dbapi_conn, connection_record):  # type: ignore[override]
        logger.debug("db.connection.released", pid=id(dbapi_conn))

    @event.listens_for(engine.sync_engine, "checkout")
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        logger.debug("db.connection.checkout", pool_size=engine.pool.size())


def get_engine() -> AsyncEngine:
    """
    Return the shared async engine, creating it if it does not yet exist.

    Thread-safety note: In async Python there is only one thread per event loop
    per process. FastAPI workers run in separate processes, each with their own
    engine instance. This is intentional and correct.
    """
    global _engine
    if _engine is None:
        _engine = _build_engine()
        logger.info("db.engine.created", url=get_settings().DATABASE_URL[:60] + "...")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Return the shared async session factory.

    Sessions are expire_on_commit=False which means loaded objects remain
    usable after commit() without emitting additional SELECT queries.
    This is correct for our read-heavy API response patterns.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a database session.

    Usage:
        async with get_db_session() as session:
            result = await session.execute(select(Node))

    Behaviour:
        - Commits the transaction if the body exits normally.
        - Rolls back and re-raises if any exception occurs.
        - Always closes the session regardless of outcome.

    FastAPI dependency injection pattern:
        Use get_db() (below) as a FastAPI Depends() instead of this
        context manager directly inside route handlers.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error(
                "db.session.rollback",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    Usage in a route:
        @router.get("/nodes")
        async def list_nodes(db: AsyncSession = Depends(get_db)):
            ...

    The session is closed automatically when the request completes.
    """
    async with get_db_session() as session:
        yield session


# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@retry(
    retry=retry_if_exception_type(OperationalError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(10),
    before_sleep=before_sleep_log(_std_logger, logging.WARNING),
    after=after_log(_std_logger, logging.INFO),
    reraise=True,
)
async def connect_with_retry() -> None:
    """
    Verify database connectivity at startup with exponential backoff.

    Retries up to 10 times with waits of 2s, 4s, 8s, 16s, 30s, 30s, ...
    This handles Railway's container startup race where the app starts
    before the DB connection is fully routed.

    Raises:
        tenacity.RetryError: If all 10 attempts fail.
        sqlalchemy.exc.OperationalError: Propagated on final failure.
    """
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        row = result.scalar()
        assert row == 1, f"Unexpected health check result: {row}"
    logger.info("db.startup.connected")


async def close_db_connections() -> None:
    """
    Gracefully dispose of all database connections.

    Called during application shutdown to allow in-flight queries to finish
    before the pool is closed. Railway sends SIGTERM on redeploy.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("db.shutdown.connections_closed")


# ─── Health Check ─────────────────────────────────────────────────────────────

async def check_db_health() -> dict:
    """
    Execute a lightweight health check query.

    Returns a dict suitable for inclusion in the /health endpoint response.
    Never raises — returns error details in the dict on failure.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) as node_count "
                    "FROM supply_chain_nodes "
                    "WHERE status = 'operational'"
                )
            )
            row = result.one()
        return {
            "status": "healthy",
            "operational_nodes": row.node_count,
            "pool_size": engine.pool.size(),
            "pool_checked_out": engine.pool.checkedout(),
        }
    except Exception as exc:
        logger.error("db.health_check.failed", error=str(exc))
        return {
            "status": "unhealthy",
            "error": str(exc),
        }
