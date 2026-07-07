"""Database connection and session management for PlantBrain."""

import logging
import os
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings


logger = logging.getLogger(__name__)
FALLBACK_SQLITE_URL = "sqlite+aiosqlite:///./data/plantbrain.db"


def _build_engine(database_url: str):
    """Create an async SQLAlchemy engine for the configured database URL."""

    is_sqlite = database_url.startswith("sqlite")
    engine_kwargs = {
        "echo": settings.environment == "development",
        "pool_pre_ping": True,
    }
    if is_sqlite:
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    try:
        return create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            **engine_kwargs,
        )
    except TypeError:
        logger.warning("Database driver rejected pool_size/max_overflow; creating engine without explicit pool sizing")
        return create_async_engine(database_url, **engine_kwargs)


async_engine = _build_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()
_active_database_url = settings.database_url


def _rebind_database(database_url: str) -> None:
    """Point future sessions at a replacement database engine."""

    global async_engine, _active_database_url
    async_engine = _build_engine(database_url)
    AsyncSessionLocal.configure(bind=async_engine)
    _active_database_url = database_url


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


async def _create_tables() -> None:
    """Create all ORM tables on the active database engine."""

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def init_db() -> None:
    """Create persistence directories and initialize database tables."""

    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs("./data", exist_ok=True)
    graph_dir = os.path.dirname(settings.graph_persist_path)
    if graph_dir:
        os.makedirs(graph_dir, exist_ok=True)

    from app.models import compliance, document, equipment, inspection, query_log  # noqa: F401

    try:
        await _create_tables()
    except Exception as exc:
        if settings.environment == "production" and not _active_database_url.startswith("sqlite"):
            logger.warning(
                "Configured SQL database is unavailable (%s); falling back to local SQLite demo storage",
                exc,
            )
            await async_engine.dispose()
            _rebind_database(FALLBACK_SQLITE_URL)
            await _create_tables()
            return
        raise