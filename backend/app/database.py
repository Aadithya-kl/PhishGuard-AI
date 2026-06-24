"""Async SQLAlchemy engine, session factory, and Base declarative class."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=NullPool,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that yields a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables and default user (for dev/testing only)."""
    # Import models to ensure they are registered with Base.metadata
    from app.models.user import User
    from app.models.scan import EmailScan, HeaderAnalysis, UrlAnalysis, AttachmentAnalysis, AiAnalysis
    from app.models.ioc import EmailIoc
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default user logic removed in Phase 11.5 for enterprise security.
    # Platform Admin must be bootstrapped via CLI.
