"""
Async SQLAlchemy engine and session factory.

Usage in FastAPI:
    from db.session import get_async_session

    async with get_async_session() as session:
        ...

Or via the FastAPI dependency in api/dependencies.py.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from chatbot.backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

is_sqlite = "sqlite" in settings.database_url
engine_kwargs = {
    "echo": settings.db_echo,
}
if not is_sqlite:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def init_db() -> None:
    """Initialize database tables on startup if they do not exist."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.warning(
            "Could not automatically initialize DB tables (%s). "
            "Please ensure your database is created and reachable.",
            exc,
        )


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for standalone use (e.g., background tasks)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
