"""
SQLAlchemy async engine and session management.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.base import Base
import app.models  # noqa: F401 — register all models with Base.metadata

settings = get_settings()
_db_url = settings.get_database_url()

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in _db_url else {},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def ensure_comment_dm_sent_table() -> None:
    """Create comment_dm_sent table if missing (Comment-to-DM dedup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_comment_dm_enabled_post_table() -> None:
    """Create comment_dm_enabled_post table if missing (Comment-to-DM per-post allowlist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_instagram_dm_allowed_user_table() -> None:
    """Create instagram_dm_allowed_user table if missing (follower allowlist for Comment-to-DM)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_task_result_message_column() -> None:
    """Add result_message to tasks if missing (works without migration 003)."""
    def _add_if_missing(sync_conn):
        from sqlalchemy import text
        is_sqlite = "sqlite" in str(sync_conn.engine.url)
        if is_sqlite:
            cursor = sync_conn.execute(text("PRAGMA table_info(tasks)"))
            rows = cursor.fetchall()
            has_col = any(r[1] == "result_message" for r in rows)
            if not has_col:
                sync_conn.execute(text("ALTER TABLE tasks ADD COLUMN result_message TEXT"))
        else:
            sync_conn.execute(text(
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS result_message TEXT"
            ))
    async with engine.begin() as conn:
        await conn.run_sync(_add_if_missing)


async def init_db() -> None:
    """Create all tables. Call on startup or via migration."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
