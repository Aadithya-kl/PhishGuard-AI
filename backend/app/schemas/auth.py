"""Authentication and user schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Requests ─────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=256)
    mfa_code: Optional[str] = Field(default=None, max_length=10)


class TokenRefreshRequest(BaseModel):
    refresh_token: Optional[str] = Field(default=None, max_length=4096)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., max_length=256)
    new_password: str = Field(..., min_length=8, max_length=128)


class TOTPVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)


class MFADisableRequest(BaseModel):
    password: str = Field(..., max_length=256)
    code: str = Field(..., min_length=6, max_length=10)


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


# ── Responses ────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    mfa_enabled: bool = False
    created_at: datetime
    updated_at: datetime


class OrganizationSummary(BaseModel):
    id: str
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    user: Optional[UserResponse] = None
    organization: Optional[OrganizationSummary] = None


class LoginResponse(BaseModel):
    mfa_required: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"  # noqa: S105
    expires_in: Optional[int] = None
    user: Optional[UserResponse] = None
    organization: Optional[OrganizationSummary] = None


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str


class ApiKeyResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    prefix: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned once on creation — includes the raw key."""
    raw_key: str
