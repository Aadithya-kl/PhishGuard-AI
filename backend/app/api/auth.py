from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegisterRequest, UserResponse, TokenResponse
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user
)
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from pydantic import BaseModel
import uuid
from app.config import settings
from app.core.rate_limit import limiter
from app.schemas.auth import UserLoginRequest, TokenRefreshRequest, LoginResponse, TOTPSetupResponse, TOTPVerifyRequest
import pyotp

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role="analyst",
        is_active=True
    )
    db.add(user)
    await db.flush()  # to get user.id
    
    # In enterprise mode, users must be invited to an organization by an Admin.
    # We do NOT create an organization or make them a platform_admin automatically.
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.mfa_enabled:
        if not body.mfa_code:
            return LoginResponse(mfa_required=True)
        else:
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(body.mfa_code):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    # Get first active membership
    membership_res = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user.id, OrganizationMember.is_active.is_(True))
    )
    membership = membership_res.scalars().first()
    
    if not membership:
        # User has no orgs. We can issue a token with no org, but let's just reject for now or issue a limited token.
        # For simplicity, if no org, role is viewer and org is empty string.
        org_id = ""
        role = "viewer"
    else:
        org_id = str(membership.organization_id)
        role = membership.role.value
        
    access_token = create_access_token(str(user.id), org_id, role)
    refresh_token = create_refresh_token(str(user.id))
    
    return LoginResponse(
        mfa_required=False,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User inactive or deleted")
            
        membership_res = await db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.user_id == user.id, OrganizationMember.is_active.is_(True))
        )
        membership = membership_res.scalars().first()
        org_id = str(membership.organization_id) if membership else ""
        role = membership.role.value if membership else "viewer"

        new_access = create_access_token(str(user.id), org_id, role)
        new_refresh = create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # In a stateless JWT setup, logout is typically handled client-side.
    # To properly revoke, we would need a token blacklist in Redis.
    # For now, we return 200 OK to signal client to drop tokens.
    return {"status": "ok", "detail": "Logged out successfully"}

@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled")
        
    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    await db.commit()
    
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="PhishGuard AI")
    return TOTPSetupResponse(secret=secret, uri=uri)

@router.post("/totp/verify")
async def verify_totp(body: TOTPVerifyRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already verified")
        
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
        
    current_user.mfa_enabled = True
    await db.commit()
    return {"status": "ok", "detail": "MFA enabled successfully"}

class SwitchOrgRequest(BaseModel):
    organization_id: uuid.UUID

@router.post("/switch-org", response_model=TokenResponse)
async def switch_organization(
    req: SwitchOrgRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify membership
    membership_res = await db.execute(
        select(OrganizationMember)
        .where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.organization_id == req.organization_id,
            OrganizationMember.is_active.is_(True)
        )
    )
    membership = membership_res.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
        
    access_token = create_access_token(str(current_user.id), str(membership.organization_id), membership.role.value)
    refresh_token = create_refresh_token(str(current_user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/organizations")
async def list_organizations(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import selectinload
    res = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id, OrganizationMember.is_active.is_(True))
        .options(selectinload(OrganizationMember.organization))
    )
    memberships = res.scalars().all()
    
    return [
        {
            "id": m.organization.id,
            "name": m.organization.name,
            "slug": m.organization.slug,
            "role": m.role.value
        }
        for m in memberships if m.organization.is_active
    ]

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
