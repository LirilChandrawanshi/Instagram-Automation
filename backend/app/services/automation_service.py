"""
Orchestrates bot actions: load task/account, check limits, run action, update status.
Used by the Celery worker. Enforces one task per account at a time and account pause.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings, get_testing_mode
from app.database import AsyncSessionLocal
from app.models.task import Task
from app.models.instagram_account import InstagramAccount
from app.models.proxy import Proxy
from app.utils.rate_limiter import can_perform_action
from app.bot.actions import (
    like_post,
    follow_user,
    comment_post,
    send_dm,
    upload_post,
    view_reel,
    ActionBlockedError,
)
from app.models.task import Task as TaskModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def _is_account_busy(db: AsyncSession, account_id: object, exclude_task_id: object) -> bool:
    """True if another task for this account is already running."""
    q = select(Task.id).where(
        Task.account_id == account_id,
        Task.status == "running",
        Task.id != exclude_task_id,
    )
    result = await db.execute(q)
    return result.scalar_one_or_none() is not None


def _success_message(task_type: str) -> str:
    """Exact message for completed tasks."""
    return {
        TaskModel.LIKE_POST: "Liked successfully",
        TaskModel.FOLLOW_USER: "Followed successfully",
        TaskModel.COMMENT_POST: "Comment posted",
        TaskModel.SEND_DM: "DM sent",
        TaskModel.UPLOAD_POST: "Post uploaded",
        TaskModel.VIEW_REEL: "Reel viewed",
    }.get(task_type, "Completed")


def _warm_up_allows_task(account: InstagramAccount, task_type: str):
    # Returns (allowed: bool, error_message: str)
    """Return (allowed, error_message). Use connected_at to derive stage."""
    connected_at = getattr(account, "connected_at", None)
    if not connected_at:
        return True, ""  # legacy account, allow
    now = _utc_now()
    conn = connected_at.replace(tzinfo=timezone.utc) if getattr(connected_at, "tzinfo") is None else connected_at
    if conn.tzinfo is None:
        conn = conn.replace(tzinfo=timezone.utc)
    days = (now - conn).days
    if days < 2:
        return False, "Account in warm-up (Day 1-2): only scroll/stories allowed"
    if days < 5:
        if task_type not in (TaskModel.LIKE_POST, TaskModel.VIEW_REEL):
            return False, "Account in warm-up (Day 3-5): only likes and reel views allowed"
        return True, ""
    if days < 10:
        if task_type not in (TaskModel.LIKE_POST, TaskModel.FOLLOW_USER, TaskModel.VIEW_REEL):
            return False, "Account in warm-up (Day 6-10): only likes, follows, and reel views"
        return True, ""
    return True, ""


class AutomationService:
    """Execute automation tasks via the bot layer."""

    @staticmethod
    async def _load_account_and_proxy(db: AsyncSession, account_id: object):
        """Load account (and proxy if set). Works even when migration 002 not run."""
        try:
            result = await db.execute(
                select(InstagramAccount)
                .options(selectinload(InstagramAccount.proxy))
                .where(InstagramAccount.id == account_id)
            )
            return result.scalar_one_or_none()
        except DatabaseError as e:
            err = (str(getattr(e, "orig", e)) + " " + str(e)).lower()
            if "no such column" not in err and "has no column" not in err:
                raise
            row = (
                await db.execute(
                    select(
                        InstagramAccount.id,
                        InstagramAccount.username,
                        InstagramAccount.session_cookie,
                        InstagramAccount.proxy_id,
                        InstagramAccount.device_profile,
                        InstagramAccount.status,
                    ).where(InstagramAccount.id == account_id)
                )
            ).one_or_none()
            if not row:
                return None
            proxy = None
            if row.proxy_id:
                proxy = (await db.execute(select(Proxy).where(Proxy.id == row.proxy_id))).scalar_one_or_none()
            out = type("AccountRow", (), {})()
            out.id = row.id
            out.username = row.username
            out.session_cookie = row.session_cookie
            out.proxy_id = row.proxy_id
            out.device_profile = row.device_profile
            out.status = row.status
            out.connected_at = None
            out.paused_until = None
            out.proxy = proxy
            return out

    @staticmethod
    async def run_task(task_id: str) -> None:
        """Load task and account, check limits, run appropriate action, update task."""
        async with AsyncSessionLocal() as db:
            task_id_val = task_id if get_settings().use_sqlite else UUID(task_id)
            result = await db.execute(select(Task).where(Task.id == task_id_val))
            task = result.scalar_one_or_none()
            if not task:
                return
            account = await AutomationService._load_account_and_proxy(db, task.account_id)
            if not account:
                task.status = "failed"
                task.result_message = "Account not found"
                await db.commit()
                return

            # One task per account at a time
            if await _is_account_busy(db, task.account_id, task.id):
                return  # leave task pending for next scheduler tick

            # Account paused (e.g. after action block) — skipped when testing mode
            if not get_testing_mode():
                paused_until = getattr(account, "paused_until", None)
                if paused_until:
                    until = paused_until.replace(tzinfo=timezone.utc) if paused_until and getattr(paused_until, "tzinfo") is None else paused_until
                    if until and _utc_now() < until:
                        msg = "Account paused until action block expires"
                        task.status = "failed"
                        task.result_message = msg
                        task.payload = (task.payload or {}) | {"error": msg}
                        await db.commit()
                        return

            # Warm-up: restrict by account age — skipped when testing mode
            if not get_testing_mode():
                allowed, warm_up_msg = _warm_up_allows_task(account, task.task_type)
                if not allowed:
                    task.status = "failed"
                    task.result_message = warm_up_msg
                    task.payload = (task.payload or {}) | {"error": warm_up_msg}
                    await db.commit()
                    return

            # Check daily limit — skipped when testing mode
            if not get_testing_mode() and not await can_perform_action(db, task.account_id, task.task_type):
                msg = "Daily limit exceeded"
                task.status = "failed"
                task.result_message = msg
                task.payload = (task.payload or {}) | {"error": msg}
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
            elif task.task_type == TaskModel.VIEW_REEL:
                await view_reel(account, task.target)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            async with AsyncSessionLocal() as db:
                res = await db.execute(select(Task).where(Task.id == task.id))
                t = res.scalar_one()
                t.status = "completed"
                t.result_message = _success_message(task.task_type)
                t.completed_at = _utc_now()
                await db.commit()
        except ActionBlockedError as e:
            from datetime import timedelta
            paused = _utc_now() + timedelta(hours=24)
            async with AsyncSessionLocal() as db:
                try:
                    await db.execute(
                        update(InstagramAccount)
                        .where(InstagramAccount.id == task.account_id)
                        .values(paused_until=paused, action_block_count=InstagramAccount.action_block_count + 1)
                    )
                except DatabaseError:
                    pass  # migration 002 not applied; columns may not exist
                res = await db.execute(select(Task).where(Task.id == task.id))
                t = res.scalar_one()
                t.status = "failed"
                t.result_message = str(e)
                t.payload = (t.payload or {}) | {"error": str(e), "paused_until": paused.isoformat()}
                await db.commit()
        except Exception as e:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(Task).where(Task.id == task.id))
                t = res.scalar_one()
                t.status = "failed"
                t.result_message = str(e)
                t.payload = (t.payload or {}) | {"error": str(e)}
                await db.commit()
