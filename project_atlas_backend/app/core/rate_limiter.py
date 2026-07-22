"""
app/core/rate_limiter.py
========================
API rate limiting using SlowAPI (ASGI wrapper around the `limits` library).

Two tiers:
  - Global:     RATE_LIMIT_PER_MINUTE requests per IP per minute (all endpoints)
  - Simulation: RATE_LIMIT_SIMULATION_PER_HOUR runs per user per hour

Key identifier: real IP extracted from X-Forwarded-For (Railway sets this).
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings


def _get_real_ip(request) -> str:  # type: ignore[no-untyped-def]
    """
    Extract the real client IP from X-Forwarded-For.

    Railway (and most reverse proxies) set X-Forwarded-For. We take the
    leftmost IP (the original client) and strip any port suffix.
    Falls back to ASGI client host if the header is absent.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # "client_ip, proxy1_ip, proxy2_ip" — take leftmost
        real_ip = forwarded_for.split(",")[0].strip()
        # Strip IPv6 brackets and port if present
        if real_ip.startswith("["):
            real_ip = real_ip.split("]")[0].lstrip("[")
        elif ":" in real_ip and real_ip.count(":") == 1:
            real_ip = real_ip.split(":")[0]
        return real_ip
    return get_remote_address(request)


# Limiter instance shared across the application
limiter = Limiter(
    key_func=_get_real_ip,
    default_limits=[],   # No default — apply per-endpoint or via middleware
    storage_uri=None,    # Resolved dynamically from settings at first use
)


def get_global_limit() -> str:
    """Return the global rate limit string in SlowAPI format."""
    cfg = get_settings()
    return f"{cfg.RATE_LIMIT_PER_MINUTE}/minute"


def get_simulation_limit() -> str:
    """Return the simulation rate limit string in SlowAPI format."""
    cfg = get_settings()
    return f"{cfg.RATE_LIMIT_SIMULATION_PER_HOUR}/hour"
