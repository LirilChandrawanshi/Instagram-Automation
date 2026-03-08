"""
Orchestrates bot actions: load task/account, check limits, run action, update status.
Used by the Celery worker.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.task import Task
from app.models.instagram_account import InstagramAccount
from app.utils.rate_limiter import can_perform_action
from app.bot.actions import (
    like_post,
    follow_user,
    comment_post,
    send_dm,
    upload_post,
)
from app.models.task import Task as TaskModel


class AutomationService:
    """Execute automation tasks via the bot layer."""

    @staticmethod
    async def run_task(task_id: str) -> None:
        """Load task and account, check limits, run appropriate action, update task."""
        async with AsyncSessionLocal() as db:
            task_id_val = task_id if get_settings().use_sqlite else UUID(task_id)
            result = await db.execute(select(Task).where(Task.id == task_id_val))
            task = result.scalar_one_or_none()
            if not task:
                return
            result = await db.execute(
                select(InstagramAccount)
                .options(selectinload(InstagramAccount.proxy))
                .where(InstagramAccount.id == task.account_id)
            )
            account = result.scalar_one_or_none()
            if not account:
                task.status = "failed"
                await db.commit()
                return

            # Check daily limit
            if not await can_perform_action(db, task.account_id, task.task_type):
                task.status = "failed"
                task.payload = (task.payload or {}) | {"error": "Daily limit exceeded"}
                await db.commit()
                return

            task.status = "running"
            await db.commit()

        try:
            if task.task_type == TaskModel.LIKE_POST:
                await like_post(account, task.target)
            elif task.task_type == TaskModel.FOLLOW_USER:
                await follow_user(account, task.target)
            elif task.task_type == TaskModel.COMMENT_POST:
                msg = (task.payload or {}).get("message", "")
                await comment_post(account, task.target, msg)
            elif task.task_type == TaskModel.SEND_DM:
                msg = (task.payload or {}).get("message", "")
                await send_dm(account, task.target, msg)
            elif task.task_type == TaskModel.UPLOAD_POST:
                path = (task.payload or {}).get("image_path", "")
                caption = (task.payload or {}).get("caption", "")
                await upload_post(account, path, caption)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            async with AsyncSessionLocal() as db:
                res = await db.execute(select(Task).where(Task.id == task.id))
                t = res.scalar_one()
                t.status = "completed"
                t.completed_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(Task).where(Task.id == task.id))
                t = res.scalar_one()
                t.status = "failed"
                t.payload = (t.payload or {}) | {"error": str(e)}
                await db.commit()
