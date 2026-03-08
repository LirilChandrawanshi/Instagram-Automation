"""
Create tasks and enqueue them to Celery (or run inline when RUN_TASKS_INLINE=true).
When inline: API returns immediately; execution runs in background. Scheduled tasks
are run by a periodic loop (see main.py lifespan).
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.task import Task
from app.schemas.task import TaskCreate
from app.bot.worker import run_automation_task
from app.services.automation_service import AutomationService
from app.core.deps import normalize_id


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_due_now(scheduled_time: Optional[datetime]) -> bool:
    """True if task should run now (no schedule or schedule in the past)."""
    if scheduled_time is None:
        return True
    now = _utc_now()
    st = scheduled_time
    if st.tzinfo is None:
        st = st.replace(tzinfo=timezone.utc)
    return st <= now


class SchedulerService:
    """Create automation tasks and send to Celery or run inline in background."""

    @staticmethod
    async def create_and_enqueue(db: AsyncSession, payload: TaskCreate) -> Task:
        """Create a Task record; enqueue to Celery or run inline in background. Returns immediately."""
        task = Task(
            account_id=normalize_id(payload.account_id),
            task_type=payload.task_type,
            target=payload.target,
            payload=payload.payload,
            status="pending",
            scheduled_time=payload.scheduled_time,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        settings = get_settings()
        if settings.run_tasks_inline:
            if _is_due_now(payload.scheduled_time):
                asyncio.create_task(AutomationService.run_task(str(task.id)))
            return task
        try:
            eta = payload.scheduled_time if payload.scheduled_time else None
            run_automation_task.apply_async(args=[str(task.id)], eta=eta)
        except Exception:
            asyncio.create_task(AutomationService.run_task(str(task.id)))
        return task

    @staticmethod
    async def run_due_scheduled_tasks() -> None:
        """Find pending tasks with scheduled_time <= now and run each in background. Call from periodic loop."""
        async with AsyncSessionLocal() as db:
            now = _utc_now()
            # Compare with naive UTC if DB stores naive
            now_naive = now.replace(tzinfo=None) if now.tzinfo else now
            result = await db.execute(
                select(Task.id).where(
                    Task.status == "pending",
                    Task.scheduled_time.isnot(None),
                    Task.scheduled_time <= now_naive,
                )
            )
            task_ids = [str(row[0]) for row in result.all()]
        for tid in task_ids:
            asyncio.create_task(AutomationService.run_task(tid))
