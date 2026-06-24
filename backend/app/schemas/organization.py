from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid

class OrganizationMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
    is_active: bool
    joined_at: datetime
    
    class Config:
        from_attributes = True

class InviteRequest(BaseModel):
    email: EmailStr
    role: str

class InviteResponse(BaseModel):
    id: uuid.UUID
    email: str
    organization_id: uuid.UUID
    role: str
    expires_at: datetime
    
    class Config:
        from_attributes = True

class AcceptInviteRequest(BaseModel):
    invitation_token: str
