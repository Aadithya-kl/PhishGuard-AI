from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.models.user import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse
from app.core.auth import generate_api_key

router = APIRouter()

@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_ORGANIZATION))
):
    """Create a new organization-scoped API key."""
    # Ensure requested permissions are a subset of the user's permissions, or they are an admin
    if not set(data.permissions).issubset(tenant.permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Cannot grant permissions you do not possess"
        )

    raw_key, key_hash, prefix = generate_api_key()
    
    expires_at = None
    if data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)
        
    api_key = ApiKey(
        user_id=tenant.user.id,
        organization_id=tenant.organization.id,
        prefix=prefix,
        key_hash=key_hash,
        name=data.name,
        permissions=data.permissions,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    # We must return the raw key ONLY ONCE here
    response_dict = ApiKeyCreateResponse.model_validate(api_key).model_dump()
    response_dict["raw_key"] = raw_key
    return response_dict

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_ORGANIZATION))
):
    """List API keys for the organization."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.organization_id == tenant.organization.id)
    )
    return result.scalars().all()

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_ORGANIZATION))
):
    """Revoke an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id, 
            ApiKey.organization_id == tenant.organization.id
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")
        
    api_key.is_active = False
    await db.commit()
