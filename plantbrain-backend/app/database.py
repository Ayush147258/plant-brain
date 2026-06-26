"""SQLite database connection and session management for PlantBrain."""

import logging
import os
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings


logger = logging.getLogger(__name__)

_engine_kwargs = {
    "echo": settings.environment == "development",
    "pool_pre_ping": True,
    "connect_args": {"check_same_thread": False},
}

try:
    async_engine = create_async_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=10,
        **_engine_kwargs,
    )
except TypeError:
    logger.warning("SQLite driver rejected pool_size/max_overflow; creating engine without explicit pool sizing")
    async_engine = create_async_engine(settings.database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and close it after use."""

    async with AsyncSessionLocal() as session:
        yield session


async def check_db_health() -> bool:
    """Return True when the database accepts a simple SELECT query."""

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return False


async def init_db() -> None:
    """Create persistence directories and initialize database tables."""

    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.graph_persist_path), exist_ok=True)

    from app.models import compliance, document, equipment, inspection, query_log  # noqa: F401

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
