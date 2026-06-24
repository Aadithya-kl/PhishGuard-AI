from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class ApiKeyCreate(BaseModel):
    name: str
    permissions: List[str]
    expires_in_days: Optional[int] = 30  # Default 30 days, None for never

class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    prefix: str
    name: str
    permissions: List[str]
    organization_id: uuid.UUID
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class ApiKeyCreateResponse(ApiKeyResponse):
    raw_key: str  # Only returned once upon creation
