"""Authentication endpoints.

Token model
-----------
* Access token  — short-lived JWT returned in the JSON body; the browser keeps it
  in memory only (never localStorage), so an XSS cannot read a long-lived secret.
* Refresh token — single-use JWT delivered as an ``HttpOnly; Secure; SameSite``
  cookie scoped to ``/api/v1/auth``. Every refresh rotates it; logout revokes it.
  Non-browser clients may still send it in the JSON body.
"""

from __future__ import annotations

import uuid
from typing import Optional

import pyotp
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.audit import log_audit_event
from app.core.auth import (
    consume_refresh_token,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    parse_uuid,
    password_policy_errors,
    revoke_refresh_token,
    verify_password,
)
from app.core.rate_limit import limiter
from app.core.token_store import token_store
from app.database import get_db
from app.models.organization import OrganizationMember
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginResponse,
    MFADisableRequest,
    TokenRefreshRequest,
    TokenResponse,
    TOTPSetupResponse,
    TOTPVerifyRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter()

_COOKIE_PATH = f"{settings.API_V1_PREFIX}/auth"
_INVALID_LOGIN = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")


# ── helpers ──────────────────────────────────────────────────────────────

def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.COOKIE_SAMESITE.lower(),
        path=_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=_COOKIE_PATH,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE.lower(),
    )


async def _active_membership(db: AsyncSession, user_id: uuid.UUID, preferred_org: Optional[uuid.UUID] = None):
    query = select(OrganizationMember).where(
        OrganizationMember.user_id == user_id, OrganizationMember.is_active.is_(True)
    ).options(selectinload(OrganizationMember.organization))
    memberships = [m for m in (await db.execute(query)).scalars().all() if m.organization and m.organization.is_active]
    if preferred_org:
        for m in memberships:
            if m.organization_id == preferred_org:
                return m
    return memberships[0] if memberships else None


def _wants_body_refresh(request: Request) -> bool:
    """Non-browser clients opt in to receiving the refresh token in the JSON body."""
    return request.headers.get("x-token-delivery", "").lower() == "body"


async def _issue_tokens(
    db: AsyncSession, user: User, response: Response, preferred_org=None, body_refresh: bool = False
) -> dict:
    membership = await _active_membership(db, user.id, preferred_org)
    org_id = str(membership.organization_id) if membership else ""
    role = membership.role.value if membership else ""
    access = create_access_token(str(user.id), org_id, role)
    refresh = await create_refresh_token(str(user.id), org_id)
    _set_refresh_cookie(response, refresh)
    return {
        "access_token": access,
        "refresh_token": refresh if body_refresh else None,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse.model_validate(user),
        "organization": (
            {"id": str(membership.organization_id), "name": membership.organization.name, "role": role}
            if membership else None
        ),
    }


async def _verify_totp(user: User, code: str) -> bool:
    if not user.totp_secret or not code or not code.strip().isdigit():
        return False
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code.strip(), valid_window=1):
        return False
    # Replay protection: each code may be used once within its validity window.
    return await token_store.set_nx(f"totp:{user.id}:{code.strip()}", "1", 120)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "0.0.0.0"


# ── endpoints ────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(request: Request, body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    if not settings.ALLOW_PUBLIC_REGISTRATION:
        raise HTTPException(status_code=403, detail="Self-registration is disabled. Ask an administrator for an invitation.")
    errors = password_policy_errors(body.password, body.email)
    if errors:
        raise HTTPException(status_code=422, detail=f"Password {', '.join(errors)}")
    email = body.email.lower()
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        # Same response shape as success would leak nothing more than a 409 does; keep it explicit.
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, hashed_password=hash_password(body.password), full_name=body.full_name.strip(), is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(request: Request, response: Response, body: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.lower()
    lock_key = f"loginfail:{email}"
    failures = int(await token_store.get(lock_key) or 0)
    if failures >= settings.LOGIN_MAX_FAILURES:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Try again in {settings.LOGIN_LOCKOUT_MINUTES} minutes.",
        )

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not verify_password(body.password, user.hashed_password if user else None) or not user or not user.is_active:
        await token_store.incr(lock_key, settings.LOGIN_LOCKOUT_MINUTES * 60)
        logger.warning(f"Failed login for {email!r} from {_client_ip(request)}")
        raise _INVALID_LOGIN

    if user.mfa_enabled:
        if not body.mfa_code:
            return LoginResponse(mfa_required=True)
        if not await _verify_totp(user, body.mfa_code):
            await token_store.incr(lock_key, settings.LOGIN_LOCKOUT_MINUTES * 60)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    await token_store.delete(lock_key)
    issued = await _issue_tokens(db, user, response, body_refresh=_wants_body_refresh(request))
    if issued["organization"]:
        await log_audit_event(
            action="auth.login",
            organization_id=uuid.UUID(issued["organization"]["id"]),
            entity_type="user",
            entity_id=str(user.id),
            user_id=user.id,
            ip_address=_client_ip(request),
        )
    return LoginResponse(mfa_required=False, **issued)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    body: Optional[TokenRefreshRequest] = None,
    cookie_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    raw = (body.refresh_token if body and body.refresh_token else None) or cookie_token
    if not raw:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = await consume_refresh_token(raw)
    except HTTPException:
        _clear_refresh_cookie(response)
        raise
    user = await db.get(User, parse_uuid(payload.get("sub")))
    if not user or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return TokenResponse(**await _issue_tokens(db, user, response, parse_uuid(payload.get("org")), _wants_body_refresh(request)))


@router.post("/logout")
async def logout(
    response: Response,
    body: Optional[TokenRefreshRequest] = None,
    cookie_token: Optional[str] = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
):
    await revoke_refresh_token((body.refresh_token if body else None) or cookie_token)
    _clear_refresh_cookie(response)
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    errors = password_policy_errors(body.new_password, current_user.email)
    if errors:
        raise HTTPException(status_code=422, detail=f"Password {', '.join(errors)}")
    current_user.hashed_password = hash_password(body.new_password)
    await db.commit()
    return {"status": "ok"}


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled")
    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    await db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name=settings.APP_NAME)
    return TOTPSetupResponse(secret=secret, uri=uri)


@router.post("/totp/verify")
@limiter.limit("10/minute")
async def verify_totp(
    request: Request,
    body: TOTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled")
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Call /totp/setup first")
    if not await _verify_totp(current_user, body.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    current_user.mfa_enabled = True
    await db.commit()
    return {"status": "ok", "detail": "MFA enabled"}


@router.post("/totp/disable")
@limiter.limit("5/minute")
async def disable_totp(
    request: Request,
    body: MFADisableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    if not verify_password(body.password, current_user.hashed_password) or not await _verify_totp(current_user, body.code):
        raise HTTPException(status_code=400, detail="Invalid password or MFA code")
    current_user.mfa_enabled = False
    current_user.totp_secret = None
    await db.commit()
    return {"status": "ok"}


class SwitchOrgRequest(BaseModel):
    organization_id: uuid.UUID


@router.post("/switch-org", response_model=TokenResponse)
async def switch_organization(
    request: Request,
    req: SwitchOrgRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = await _active_membership(db, current_user.id, req.organization_id)
    if not membership or membership.organization_id != req.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
    return TokenResponse(**await _issue_tokens(db, current_user, response, req.organization_id, _wants_body_refresh(request)))


@router.get("/organizations")
async def list_organizations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id, OrganizationMember.is_active.is_(True))
        .options(selectinload(OrganizationMember.organization))
    )
    return [
        {"id": str(m.organization.id), "name": m.organization.name, "slug": m.organization.slug, "role": m.role.value}
        for m in res.scalars().all()
        if m.organization and m.organization.is_active
    ]
