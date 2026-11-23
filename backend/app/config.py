"""Application configuration loaded from environment variables via pydantic-settings.

Security notes
--------------
* ``SECRET_KEY`` signs every JWT. In production the app refuses to start if it is
  missing, shorter than 32 characters, or one of the known placeholder values.
* ``JWT_SECRET_KEY`` is accepted as an alias because older ``.env`` files used it.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRETS = {
    "",
    "super-secret-key-change-in-production-please",
    "your-super-secret-key-change-in-production-min-32-chars",
    "your-jwt-secret-key-change-in-production",
    "change-me",
    "changeme",
}

_DEV_FALLBACK_SECRET = "dev-only-insecure-secret-key-do-not-use-in-production-0000"  # noqa: S105 (dev only, refused in prod)


class Settings(BaseSettings):
    """Central configuration for PhishGuard AI backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "PhishGuard AI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"))
    API_V1_PREFIX: str = "/api/v1"
    OBSERVATION_MODE: bool = True  # Response actions are simulated unless explicitly disabled

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://phishguard:phishguard@localhost:5432/phishguard_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT / Auth ───────────────────────────────────────────────────────
    SECRET_KEY: str = Field(default="", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET_KEY"))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, validation_alias=AliasChoices("REFRESH_TOKEN_EXPIRE_DAYS", "JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    )
    JWT_ISSUER: str = "phishguard-ai"
    JWT_AUDIENCE: str = "phishguard-api"

    # Refresh-token cookie
    REFRESH_COOKIE_NAME: str = "pg_refresh"
    COOKIE_SECURE: Optional[bool] = None  # defaults to True in production
    COOKIE_SAMESITE: str = "strict"

    # Account policy
    ALLOW_PUBLIC_REGISTRATION: bool = False
    PASSWORD_MIN_LENGTH: int = 12
    LOGIN_MAX_FAILURES: int = 10
    LOGIN_LOCKOUT_MINUTES: int = 15

    # ── Celery ───────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── External APIs ────────────────────────────────────────────────────
    VIRUSTOTAL_API_KEY: Optional[str] = None
    SAFEBROWSING_API_KEY: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("SAFEBROWSING_API_KEY", "GOOGLE_SAFE_BROWSING_API_KEY")
    )
    ABUSEIPDB_API_KEY: Optional[str] = None
    OTX_API_KEY: Optional[str] = None
    PHISHTANK_API_KEY: Optional[str] = None

    # ── LLM providers ────────────────────────────────────────────────────
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_PROVIDER: str = "gemini"  # "gemini", "ollama", "openai", "mock"

    # ── File storage ─────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── Rate limiting ────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_SCAN_PER_MINUTE: int = 20
    RATE_LIMIT_STORAGE_URI: Optional[str] = None  # e.g. redis://redis:6379/3; defaults to memory

    # ── HTTP hardening ───────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"
    TRUSTED_HOSTS: str = "*"
    ENABLE_API_DOCS: Optional[bool] = None  # defaults to False in production
    METRICS_TOKEN: Optional[str] = None  # when set, /metrics requires "Authorization: Bearer <token>"

    # ── Derived helpers ──────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]

    @property
    def trusted_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()] or ["*"]

    @property
    def cookie_secure(self) -> bool:
        return self.is_production if self.COOKIE_SECURE is None else self.COOKIE_SECURE

    @property
    def docs_enabled(self) -> bool:
        return (not self.is_production) if self.ENABLE_API_DOCS is None else self.ENABLE_API_DOCS

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        secret_weak = self.SECRET_KEY in _PLACEHOLDER_SECRETS or len(self.SECRET_KEY) < 32
        if self.is_production:
            if secret_weak:
                raise ValueError(
                    "SECRET_KEY must be set to a random value of at least 32 characters in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS may not contain '*' in production")
        elif secret_weak:
            # Development convenience only — loudly flagged at startup in main.py
            self.SECRET_KEY = _DEV_FALLBACK_SECRET
        if self.COOKIE_SAMESITE.lower() not in {"strict", "lax", "none"}:
            raise ValueError("COOKIE_SAMESITE must be strict, lax or none")
        return self

    @property
    def using_dev_secret(self) -> bool:
        return self.SECRET_KEY == _DEV_FALLBACK_SECRET


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()


settings = get_settings()
