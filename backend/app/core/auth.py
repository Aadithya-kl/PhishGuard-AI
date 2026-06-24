"""JWT authentication, password hashing, and user dependency injection."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import ApiKey, User

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ── Password helpers ─────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ──────────────────────────────────────────────────────────

def create_access_token(user_id: str, org_id: str, role: str) -> str:
    """Create a short-lived access JWT."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "org": org_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh JWT."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT, raising on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── API-key helpers ──────────────────────────────────────────────────────

def generate_api_key() -> tuple[str, str, str]:
    """Return (raw_key, key_hash, prefix)."""
    raw = f"pg_{secrets.token_urlsafe(32)}"
    prefix = raw[:8]
    hashed = pwd_context.hash(raw)
    return raw, hashed, prefix


async def _resolve_api_key(token: str, db: AsyncSession) -> Optional[User]:
    """Try to resolve an API key to a user."""
    if not token.startswith("pg_"):
        return None
    prefix = token[:8]
    result = await db.execute(select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.is_active.is_(True)))
    api_keys = result.scalars().all()
    for api_key in api_keys:
        if pwd_context.verify(token, api_key.key_hash):
            if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                return None
            result2 = await db.execute(select(User).where(User.id == api_key.user_id))
            return result2.scalar_one_or_none()
    return None


# ── FastAPI dependencies ─────────────────────────────────────────────────

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current user from JWT or API key.

    Raises 401 if authentication fails.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if it's an API key
    if token.startswith("pg_"):
        user = await _resolve_api_key(token, db)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        return user

    # Otherwise treat as JWT
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Same as get_current_user but returns None instead of raising."""
    if token is None:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

def require_role(allowed_roles: list[str]):
    async def role_checker(current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
        payload = decode_token(token)
        token_role = payload.get("role")
        if token_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires one of: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
