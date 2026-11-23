"""JWT authentication, password hashing, API keys and user dependency injection."""

from __future__ import annotations

import hashlib
import hmac
import re
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
from app.core.token_store import token_store
from app.database import get_db
from app.models.user import ApiKey, User

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)

API_KEY_PREFIX = "pg_"
# Pre-computed hash used to keep login timing constant when the e-mail does not exist.
_DUMMY_HASH = pwd_context.hash(secrets.token_urlsafe(16))

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# ── Password helpers ─────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: Optional[str]) -> bool:
    """Constant-time-ish verification; always runs a bcrypt round."""
    if not hashed:
        pwd_context.verify(plain, _DUMMY_HASH)
        return False
    try:
        return pwd_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False


_COMMON_PASSWORDS = {"password", "password1", "123456789012", "qwertyuiop12", "phishguard@2024!", "letmein12345"}


def password_policy_errors(password: str, email: str = "") -> list[str]:
    """Return human-readable reasons a password is too weak (empty list = OK)."""
    errors: list[str] = []
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"must be at least {settings.PASSWORD_MIN_LENGTH} characters")
    if len(password) > 128:
        errors.append("must be at most 128 characters")
    classes = sum(bool(re.search(p, password)) for p in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"))
    if classes < 3:
        errors.append("must contain at least three of: lowercase, uppercase, digit, symbol")
    if password.lower() in _COMMON_PASSWORDS:
        errors.append("is too common")
    local = email.split("@")[0].lower() if email else ""
    if local and len(local) >= 4 and local in password.lower():
        errors.append("must not contain your e-mail name")
    return errors


# ── JWT helpers ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, org_id: str, role: str) -> str:
    """Create a short-lived access JWT.

    The role claim is informational for the UI only — authorization is always
    re-derived from the database membership on every request.
    """
    now = _now()
    payload = {
        "sub": user_id,
        "org": org_id,
        "role": role,
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def create_refresh_token(user_id: str, org_id: str = "") -> str:
    """Create a single-use refresh JWT and register its id in the allow-list."""
    now = _now()
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    jti = secrets.token_urlsafe(24)
    payload = {
        "sub": user_id,
        "org": org_id,
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
        "jti": jti,
    }
    await token_store.set(f"rt:{jti}", user_id, ttl)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Decode and validate a JWT. Never leaks the underlying error to clients."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except JWTError:
        raise _CREDENTIALS_EXC
    if payload.get("type") != expected_type:
        raise _CREDENTIALS_EXC
    return payload


async def consume_refresh_token(token: str) -> dict:
    """Validate a refresh token and burn it (rotation). Reuse => 401."""
    payload = decode_token(token, expected_type="refresh")
    jti = payload.get("jti")
    if not jti:
        raise _CREDENTIALS_EXC
    owner = await token_store.pop(f"rt:{jti}")
    if owner is None or owner != payload.get("sub"):
        raise _CREDENTIALS_EXC
    return payload


async def revoke_refresh_token(token: Optional[str]) -> None:
    if not token:
        return
    try:
        payload = decode_token(token, expected_type="refresh")
    except HTTPException:
        return
    if payload.get("jti"):
        await token_store.delete(f"rt:{payload['jti']}")


def parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


# ── API-key helpers ──────────────────────────────────────────────────────

def _sha256(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Return (raw_key, key_hash, prefix).

    API keys carry 256 bits of entropy, so a fast SHA-256 digest is the right
    storage primitive (bcrypt only slows down every authenticated request).
    """
    raw = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    return raw, _sha256(raw), raw[:8]


def _verify_api_key(raw: str, stored_hash: str) -> bool:
    if stored_hash.startswith("$2"):  # legacy bcrypt-hashed keys
        try:
            return pwd_context.verify(raw, stored_hash)
        except ValueError:
            return False
    return hmac.compare_digest(_sha256(raw), stored_hash)


async def resolve_api_key(token: str, db: AsyncSession) -> Optional[ApiKey]:
    """Return the active, unexpired ApiKey row matching ``token`` (or None)."""
    if not token.startswith(API_KEY_PREFIX) or len(token) > 128:
        return None
    result = await db.execute(
        select(ApiKey).where(ApiKey.prefix == token[:8], ApiKey.is_active.is_(True))
    )
    for api_key in result.scalars().all():
        if _verify_api_key(token, api_key.key_hash):
            if api_key.expires_at and api_key.expires_at < _now():
                return None
            return api_key
    return None


# ── FastAPI dependencies ─────────────────────────────────────────────────

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current user from an access JWT or API key."""
    if not token:
        raise _CREDENTIALS_EXC

    if token.startswith(API_KEY_PREFIX):
        api_key = await resolve_api_key(token, db)
        if api_key is None or api_key.user_id is None:
            raise _CREDENTIALS_EXC
        user = await db.get(User, api_key.user_id)
    else:
        payload = decode_token(token)
        user_id = parse_uuid(payload.get("sub"))
        if user_id is None:
            raise _CREDENTIALS_EXC
        user = await db.get(User, user_id)

    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if token is None:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
