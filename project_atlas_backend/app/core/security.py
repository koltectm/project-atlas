"""
app/core/security.py
====================
Authentication and authorisation utilities.

JWT lifecycle:
    Access token  — short-lived (default 60 min), carries user_id + role
    Refresh token — long-lived (default 7 days), used to rotate access tokens

passlib/bcrypt note:
    passlib 1.7.4 emits a DeprecationWarning about the `crypt` module on
    Python 3.12 (module removed in 3.13). The warning is suppressed below
    because the bcrypt backend does NOT use `crypt`; it uses the C-level
    bcrypt library directly. The warning is a false positive.
"""

from __future__ import annotations

import warnings
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

# Suppress the passlib/crypt deprecation warning on Python 3.12
warnings.filterwarnings(
    "ignore",
    message=".*crypt.*",
    category=DeprecationWarning,
    module="passlib",
)

logger = structlog.get_logger(__name__)

# ── Password Hashing ──────────────────────────────────────────────────────────

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,          # OWASP recommendation: ≥10 rounds; 12 for server-side
)


def hash_password(plain: str) -> str:
    """
    Hash a plaintext password using bcrypt (12 rounds).

    Args:
        plain: Plaintext password string.

    Returns:
        bcrypt hash string suitable for storage in the database.
    """
    if not plain or len(plain) < 8:
        raise ValueError("Password must be at least 8 characters.")
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.

    Returns False (not raises) on mismatch — safe for constant-time comparison.
    """
    return _pwd_context.verify(plain, hashed)


# ── JWT Token Creation ────────────────────────────────────────────────────────

def _build_token(
    subject: str,
    token_type: str,
    extra_claims: dict[str, Any],
    expires_delta: timedelta,
) -> str:
    """
    Internal: Build a signed JWT with standard claims.

    Standard claims (RFC 7519):
        sub  — subject (user UUID as string)
        iat  — issued-at (UTC)
        exp  — expiry (UTC)
        jti  — JWT ID (unique per token, enables revocation tracking)
        type — "access" or "refresh" (non-standard, Atlas-specific)
    """
    cfg = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
        "type": token_type,
        **extra_claims,
    }
    return jwt.encode(payload, cfg.SECRET_KEY, algorithm=cfg.ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        user_id: UUID string of the authenticated user.
        role:    User's RBAC role ("admin" | "analyst" | "viewer").

    Returns:
        Signed JWT string.
    """
    cfg = get_settings()
    token = _build_token(
        subject=user_id,
        token_type="access",
        extra_claims={"role": role},
        expires_delta=timedelta(minutes=cfg.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.debug("security.access_token.created", user_id=user_id, role=role)
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived JWT refresh token.

    Refresh tokens carry no role claim — the role is always re-fetched from
    the database when the access token is rotated, so role changes take effect
    at the next refresh without requiring re-login.
    """
    cfg = get_settings()
    return _build_token(
        subject=user_id,
        token_type="refresh",
        extra_claims={},
        expires_delta=timedelta(days=cfg.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# ── JWT Token Validation ──────────────────────────────────────────────────────

def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Validates:
        - Signature (using SECRET_KEY + ALGORITHM)
        - Expiry (exp claim)
        - Token type must be "access"

    Args:
        token: Raw JWT string (without "Bearer " prefix).

    Returns:
        Decoded payload dict containing at minimum: sub, role, exp, jti.

    Raises:
        TokenExpiredError:  exp claim is in the past.
        InvalidTokenError:  Signature invalid, malformed, or wrong token type.
    """
    cfg = get_settings()
    try:
        payload = jwt.decode(
            token,
            cfg.SECRET_KEY,
            algorithms=[cfg.ALGORITHM],
            options={"verify_exp": True},
        )
    except JWTError as exc:
        error_str = str(exc).lower()
        if "expired" in error_str or "exp" in error_str:
            raise TokenExpiredError() from exc
        raise InvalidTokenError(detail=str(exc)) from exc

    if payload.get("type") != "access":
        raise InvalidTokenError(
            message="Token type mismatch. Expected 'access' token.",
            detail={"received_type": payload.get("type")},
        )

    if not payload.get("sub"):
        raise InvalidTokenError(message="Token missing 'sub' claim.")

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT refresh token.

    Raises:
        TokenExpiredError:  Refresh token has expired (user must log in again).
        InvalidTokenError:  Malformed or wrong token type.
    """
    cfg = get_settings()
    try:
        payload = jwt.decode(
            token,
            cfg.SECRET_KEY,
            algorithms=[cfg.ALGORITHM],
            options={"verify_exp": True},
        )
    except JWTError as exc:
        error_str = str(exc).lower()
        if "expired" in error_str:
            raise TokenExpiredError(
                message="Refresh token has expired. Please log in again."
            ) from exc
        raise InvalidTokenError(detail=str(exc)) from exc

    if payload.get("type") != "refresh":
        raise InvalidTokenError(
            message="Token type mismatch. Expected 'refresh' token.",
        )

    return payload


# ── Token Extraction Helpers ──────────────────────────────────────────────────

def extract_token_from_header(authorization: str | None) -> str:
    """
    Extract the raw token string from an Authorization header.

    Accepts:
        "Bearer <token>"
        "<token>"  (bare token, accepted for convenience)

    Args:
        authorization: Value of the Authorization HTTP header.

    Returns:
        Raw JWT string.

    Raises:
        InvalidTokenError: Header is missing or malformed.
    """
    if not authorization:
        raise InvalidTokenError(message="Authorization header is missing.")
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    else:
        token = authorization.strip()
    if not token:
        raise InvalidTokenError(message="Authorization header is empty after stripping 'Bearer' prefix.")
    return token
