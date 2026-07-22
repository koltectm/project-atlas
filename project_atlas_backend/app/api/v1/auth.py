"""
app/api/v1/auth.py
==================
Authentication endpoints: login, token refresh, logout, profile management.
"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Request
from sqlalchemy import select, text
from app.dependencies import DbSession, CurrentUser, CurrentUserId
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshRequest,
    UserProfileResponse, UserProfileUpdate, RoleUpdateRequest,
)
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_refresh_token
from app.core.audit import write_audit_log
from app.core.exceptions import AuthenticationError, InsufficientRoleError
from app.db.models import UserProfile, UserRoleEnum
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Obtain JWT access + refresh tokens")
async def login(body: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    """
    Authenticate with email + password via Supabase Auth.

    Returns a short-lived access token and a long-lived refresh token.
    The access token must be sent as `Authorization: Bearer <token>` on
    subsequent requests.
    """
    from supabase import create_client
    cfg = get_settings()

    try:
        supa = create_client(cfg.supabase_url_str, cfg.SUPABASE_ANON_KEY)
        auth_response = supa.auth.sign_in_with_password({
            "email": str(body.email),
            "password": body.password,
        })
    except Exception as exc:
        raise AuthenticationError(message="Invalid email or password.") from exc

    if not auth_response.user:
        raise AuthenticationError(message="Invalid email or password.")

    user_id  = auth_response.user.id
    profile  = (await db.execute(
        select(UserProfile).where(UserProfile.profile_id == uuid.UUID(user_id))
    )).scalar_one_or_none()
    role     = profile.role.value if profile else "viewer"

    # Update last_active
    if profile:
        profile.last_active = text("NOW()")
        await db.flush()

    access_token  = create_access_token(user_id=user_id, role=role)
    refresh_token = create_refresh_token(user_id=user_id)

    await write_audit_log(
        db=db, user_id=user_id, action="LOGIN",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    cfg2 = get_settings()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=cfg2.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotate access token using refresh token")
async def refresh_token(body: RefreshRequest, db: DbSession) -> TokenResponse:
    """Validate the refresh token and issue a new access token."""
    payload = decode_refresh_token(body.refresh_token)
    user_id = payload["sub"]

    profile = (await db.execute(
        select(UserProfile).where(UserProfile.profile_id == uuid.UUID(user_id))
    )).scalar_one_or_none()
    role = profile.role.value if profile else "viewer"

    cfg = get_settings()
    return TokenResponse(
        access_token=create_access_token(user_id=user_id, role=role),
        refresh_token=create_refresh_token(user_id=user_id),
        token_type="bearer",
        expires_in=cfg.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
async def get_me(user: CurrentUser, db: DbSession) -> UserProfileResponse:
    user_id = uuid.UUID(user["sub"])
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.profile_id == user_id)
    )).scalar_one_or_none()
    if not profile:
        raise AuthenticationError(message="User profile not found.")
    return UserProfileResponse.model_validate(profile)


@router.patch("/me", response_model=UserProfileResponse, summary="Update current user profile")
async def update_me(
    body: UserProfileUpdate, user: CurrentUser, db: DbSession
) -> UserProfileResponse:
    user_id = uuid.UUID(user["sub"])
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.profile_id == user_id)
    )).scalar_one_or_none()
    if not profile:
        raise AuthenticationError(message="User profile not found.")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    await db.flush()
    return UserProfileResponse.model_validate(profile)
