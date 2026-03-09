"""
Daily action limits per account to simulate human behavior.
Uses in-memory or Redis-backed counters; here we use DB for simplicity.
"""
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.task import Task


def _get_limit(task_type: str) -> int | None:
    """Return daily limit for task_type (fresh from settings). None = no limit."""
    settings = get_settings()
    limits = {
        Task.LIKE_POST: settings.daily_limit_likes,
        Task.FOLLOW_USER: settings.daily_limit_follows,
        Task.SEND_DM: settings.daily_limit_dms,
        Task.COMMENT_POST: settings.daily_limit_comments,
        Task.UPLOAD_POST: 10,
        Task.VIEW_REEL: getattr(settings, "daily_limit_reel_views", 9999),
    }
    return limits.get(task_type)


async def get_today_count(
    db: AsyncSession,
    account_id: UUID,
    task_type: str,
) -> int:
    """Return number of completed tasks of this type for this account today."""
    today = date.today()
    result = await db.execute(
        select(func.count(Task.id)).where(
            Task.account_id == account_id,
            Task.task_type == task_type,
            Task.status == "completed",
            func.date(Task.completed_at) == today,
        )
    )
    return result.scalar() or 0


async def can_perform_action(
    db: AsyncSession,
    account_id: UUID,
    task_type: str,
) -> bool:
    """Check if account is within daily limit for this task type."""
    limit = _get_limit(task_type)
    if limit is None:
        return True
    count = await get_today_count(db, account_id, task_type)
    return count < limit
