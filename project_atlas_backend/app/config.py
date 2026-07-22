"""
app/config.py
=============
Centralised application configuration loaded from environment variables.

All required variables are validated at startup. Missing or invalid values
raise a descriptive ValidationError before the application accepts traffic.

Environment variable loading order (highest priority first):
  1. Actual environment variables (set by Railway/Docker)
  2. .env file (local development only)
  3. Pydantic field defaults (only for optional settings)
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from pydantic import (
    AnyHttpUrl,
    Field,
    PostgresDsn,
    RedisDsn,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All fields with no default value are REQUIRED — the application will
    refuse to start if they are absent. Fields with defaults are optional.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,   # DATABASE_URL and database_url are equivalent
        extra="ignore",         # Ignore undeclared env vars (Railway injects many)
    )

    # ── Environment ────────────────────────────────────────────────────────────
    ENVIRONMENT: str = Field(
        default="development",
        pattern=r"^(development|staging|production)$",
        description="Runtime environment; affects logging verbosity and error detail",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    # ── Supabase ───────────────────────────────────────────────────────────────
    SUPABASE_URL: AnyHttpUrl = Field(
        description="Supabase project URL, e.g. https://<ref>.supabase.co",
    )
    SUPABASE_ANON_KEY: str = Field(
        min_length=100,
        description="Supabase anon/public JWT. Safe for client-side use.",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        min_length=100,
        description="Supabase service role JWT. NEVER expose to clients. Bypasses RLS.",
    )

    # ── PostgreSQL Database ────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        description=(
            "PostgreSQL connection string for the async SQLAlchemy engine. "
            "Use the Supabase Transaction Pooler URL (port 6543) on Railway."
        ),
    )
    DATABASE_URL_DIRECT: str | None = Field(
        default=None,
        description=(
            "Direct PostgreSQL connection (port 5432). "
            "Used only by Alembic migrations. Optional if same as DATABASE_URL."
        ),
    )
    DB_POOL_SIZE_MIN: int = Field(default=5, ge=1, le=50)
    DB_POOL_SIZE_MAX: int = Field(default=20, ge=5, le=100)
    DB_POOL_TIMEOUT_SECONDS: int = Field(default=30, ge=5, le=120)
    DB_ECHO_SQL: bool = Field(
        default=False,
        description="Echo all SQL statements to logs. Enable only in development.",
    )

    # ── JWT / Security ─────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        min_length=32,
        description=(
            "HMAC secret for signing JWTs. "
            "Generate with: openssl rand -hex 32"
        ),
    )
    ALGORITHM: str = Field(
        default="HS256",
        pattern=r"^(HS256|HS384|HS512|RS256)$",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        ge=5,
        le=1440,  # max 24 hours
        description="JWT access token lifetime in minutes.",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)

    # ── Redis / Celery ─────────────────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description=(
            "Redis connection URL for Celery broker and result backend. "
            "Required for async simulation jobs."
        ),
    )
    CELERY_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    CELERY_TASK_TIMEOUT_SECONDS: int = Field(default=600, ge=60, le=3600)

    # ── CORS ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description=(
            "List of allowed CORS origins. "
            "Set to Vercel frontend URL in production. "
            "Can be a JSON array string or comma-separated."
        ),
    )

    # ── Rate Limiting ──────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Global API rate limit per IP per minute.",
    )
    RATE_LIMIT_SIMULATION_PER_HOUR: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max simulation runs per user per hour.",
    )

    # ── Simulation Engine ──────────────────────────────────────────────────────
    DEFAULT_SIMULATION_ITERATIONS: int = Field(
        default=10_000,
        ge=100,
        le=100_000,
    )
    MAX_SIMULATION_ITERATIONS: int = Field(
        default=100_000,
        ge=1_000,
        le=1_000_000,
    )
    SIMULATION_TIMEOUT_SECONDS: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Hard timeout for a simulation run before it is marked failed.",
    )
    CRUDE_PRICE_USD_PER_BARREL: float = Field(
        default=82.50,
        ge=10.0,
        le=500.0,
        description="Brent crude price used in production loss calculations.",
    )
    HOLDING_COST_USD_PER_BARREL_DAY: float = Field(
        default=0.50,
        ge=0.01,
        le=10.0,
        description="Daily inventory holding cost per barrel.",
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = Field(default="Project Atlas API")
    APP_VERSION: str = Field(default="1.0.0")
    API_V1_PREFIX: str = Field(default="/api/v1")
    DOCS_ENABLED: bool = Field(
        default=True,
        description=(
            "Enable /docs and /redoc endpoints. "
            "Disable in production if the API is not public."
        ),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Validators
    # ─────────────────────────────────────────────────────────────────────────

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """
        Accept CORS_ORIGINS as either:
          - A JSON array string: '["https://example.com"]'
          - A comma-separated string: "https://a.com,https://b.com"
          - Already a list (when loaded from a .env parsing library)
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"CORS_ORIGINS is not valid JSON: {v!r}"
                    ) from exc
            # Comma-separated fallback
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        raise TypeError(f"CORS_ORIGINS must be a list or string, got {type(v)}")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_and_normalise_db_url(cls, v: str) -> str:
        """
        SQLAlchemy async engine requires the asyncpg driver dialect.
        Accept both 'postgresql://' and 'postgresql+asyncpg://' inputs.
        The sync 'postgresql://' prefix is silently upgraded.
        """
        if not isinstance(v, str) or not v.strip():
            raise ValueError("DATABASE_URL must be a non-empty string")
        v = v.strip()
        # Replace psycopg2/pg8000 style URLs for asyncpg compatibility
        if v.startswith("postgresql://") or v.startswith("postgres://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        if "asyncpg" not in v:
            raise ValueError(
                "DATABASE_URL must use the asyncpg driver: "
                "postgresql+asyncpg://user:pass@host:port/db"
            )
        return v

    @field_validator("DATABASE_URL_DIRECT", mode="before")
    @classmethod
    def validate_direct_db_url(cls, v: str | None) -> str | None:
        """
        The direct URL for Alembic uses the psycopg2 (sync) driver.
        Accept 'postgresql://', 'postgres://', or 'postgresql+psycopg2://'.
        """
        if v is None:
            return None
        v = v.strip()
        if v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql+asyncpg://", "postgresql://", 1)
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v

    @model_validator(mode="after")
    def validate_pool_sizes(self) -> "Settings":
        """Pool min must not exceed pool max."""
        if self.DB_POOL_SIZE_MIN > self.DB_POOL_SIZE_MAX:
            raise ValueError(
                f"DB_POOL_SIZE_MIN ({self.DB_POOL_SIZE_MIN}) must be ≤ "
                f"DB_POOL_SIZE_MAX ({self.DB_POOL_SIZE_MAX})"
            )
        return self

    @model_validator(mode="after")
    def validate_simulation_iterations(self) -> "Settings":
        """Default iterations must not exceed maximum."""
        if self.DEFAULT_SIMULATION_ITERATIONS > self.MAX_SIMULATION_ITERATIONS:
            raise ValueError(
                f"DEFAULT_SIMULATION_ITERATIONS ({self.DEFAULT_SIMULATION_ITERATIONS}) "
                f"must be ≤ MAX_SIMULATION_ITERATIONS ({self.MAX_SIMULATION_ITERATIONS})"
            )
        return self

    @model_validator(mode="after")
    def warn_if_debug_in_production(self) -> "Settings":
        """Emit a loud warning if debug options are enabled in production."""
        if self.ENVIRONMENT == "production":
            if self.DB_ECHO_SQL:
                logging.getLogger(__name__).warning(
                    "DB_ECHO_SQL=True in production will log all SQL to stdout. "
                    "This is a security and performance risk. Set DB_ECHO_SQL=False."
                )
            if self.DOCS_ENABLED:
                logging.getLogger(__name__).info(
                    "DOCS_ENABLED=True in production: /docs and /redoc are publicly accessible."
                )
        return self

    # ─────────────────────────────────────────────────────────────────────────
    # Computed properties
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """True when running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def alembic_database_url(self) -> str:
        """
        Synchronous database URL for Alembic migrations.
        Falls back to DATABASE_URL with asyncpg replaced by psycopg2.
        """
        if self.DATABASE_URL_DIRECT:
            return self.DATABASE_URL_DIRECT
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    @property
    def supabase_url_str(self) -> str:
        """Return SUPABASE_URL as a plain string (not AnyHttpUrl object)."""
        return str(self.SUPABASE_URL)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    The @lru_cache ensures Settings is parsed exactly once at startup.
    In tests, call get_settings.cache_clear() before patching environment
    variables to force re-parsing.

    Raises:
        pydantic.ValidationError: If any required env var is missing or invalid.
    """
    return Settings()


# Module-level alias for convenience in imports
settings = get_settings()
