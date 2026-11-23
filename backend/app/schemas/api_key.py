import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    permissions: List[str] = Field(..., min_length=1, max_length=20)
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)

    @field_validator("permissions")
    @classmethod
    def _known(cls, v: List[str]) -> List[str]:
        from app.core.tenant_context import Permission

        unknown = set(v) - Permission.all()
        if unknown:
            raise ValueError(f"Unknown permissions: {sorted(unknown)}")
        return sorted(set(v))


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    prefix: str
    name: str
    permissions: List[str]
    organization_id: uuid.UUID
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool


class ApiKeyCreateResponse(ApiKeyResponse):
    raw_key: str  # Only returned once upon creation
