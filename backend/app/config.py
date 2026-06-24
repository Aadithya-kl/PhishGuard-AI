"""Application configuration loaded from environment variables via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for PhishGuard AI backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "PhishGuard AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    OBSERVATION_MODE: bool = True  # Hardcoded safety guardrail for Phase 9

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://phishguard:phishguard_secret@localhost:5432/phishguard_db"
    DATABASE_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT / Auth ───────────────────────────────────────────────────────
    SECRET_KEY: str = "super-secret-key-change-in-production-please"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Admin seed ───────────────────────────────────────────────────────
    # Removed in Phase 11.5 for Enterprise Security Compliance

    # ── Celery ───────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── External APIs ────────────────────────────────────────────────────
    VIRUSTOTAL_API_KEY: Optional[str] = None
    SAFEBROWSING_API_KEY: Optional[str] = None
    ABUSEIPDB_API_KEY: Optional[str] = None
    OTX_API_KEY: Optional[str] = None
    PHISHTANK_API_KEY: Optional[str] = None

    # ── OpenAI / LLM / Gemini / OpenRouter ──────────────────────────────
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_PROVIDER: str = "gemini"  # "gemini", "ollama", "openai", "mock"

    # ── File storage ─────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = 25

    # ── Rate limiting ────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()

settings = get_settings()
