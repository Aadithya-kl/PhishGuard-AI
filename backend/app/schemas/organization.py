import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
    is_active: bool
    joined_at: datetime
    email: Optional[str] = None
    full_name: Optional[str] = None


class InviteRequest(BaseModel):
    email: EmailStr
    role: str


class InviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    organization_id: uuid.UUID
    role: str
    status: str
    expires_at: datetime


class InviteCreatedResponse(InviteResponse):
    """Returned once on creation — the admin shares this token/link with the invitee."""
    invitation_token: str


class AcceptInviteRequest(BaseModel):
    invitation_token: str = Field(..., min_length=16, max_length=128)


class InviteRegisterRequest(BaseModel):
    invitation_token: str = Field(..., min_length=16, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class MemberUpdateRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
