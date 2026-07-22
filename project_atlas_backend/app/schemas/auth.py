"""app/schemas/auth.py — Pydantic schemas for authentication."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.db.models import UserRoleEnum


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id:            uuid.UUID
    full_name:             str
    organization:          Optional[str]
    job_title:             Optional[str]
    role:                  UserRoleEnum
    api_calls_today:       int
    daily_api_limit:       int
    last_active:           Optional[datetime]
    total_simulations_run: int
    created_at:            datetime


class UserProfileUpdate(BaseModel):
    full_name:    Optional[str] = Field(default=None, max_length=255)
    organization: Optional[str] = Field(default=None, max_length=255)
    job_title:    Optional[str] = Field(default=None, max_length=255)
    preferences:  Optional[dict] = None


class RoleUpdateRequest(BaseModel):
    """Admin-only: change a user's role."""
    user_id: uuid.UUID
    role:    UserRoleEnum
