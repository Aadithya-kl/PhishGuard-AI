"""Async SQLAlchemy engine, session factory, and Base declarative class."""

from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# Celery tasks run each job in a fresh event loop (asyncio.run), so pooled
# connections would be bound to a dead loop. Workers therefore use NullPool;
# the API process keeps a real connection pool.
_IS_WORKER = os.environ.get("PHISHGUARD_WORKER", "").lower() in {"1", "true", "yes"}

if _IS_WORKER:
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO, poolclass=NullPool)
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (dev/testing only — production uses Alembic)."""
    import app.models  # noqa: F401  (registers every model on Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
