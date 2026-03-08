"""
Analytics API: overview stats for the dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.instagram_account import InstagramAccount
from app.models.task import Task
from app.core.deps import get_current_user, normalize_id

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Return overview stats: account count, tasks by type and status."""
    # Total accounts
    acc_result = await db.execute(
        select(func.count(InstagramAccount.id)).where(InstagramAccount.user_id == normalize_id(user.id))
    )
    total_accounts = acc_result.scalar() or 0

    # Tasks by status (only for user's accounts)
    status_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .join(InstagramAccount)
        .where(InstagramAccount.user_id == normalize_id(user.id))
        .group_by(Task.status)
    )
    tasks_by_status = {row[0]: row[1] for row in status_result.all()}

    # Tasks by type
    type_result = await db.execute(
        select(Task.task_type, func.count(Task.id))
        .join(InstagramAccount)
        .where(InstagramAccount.user_id == normalize_id(user.id))
        .group_by(Task.task_type)
    )
    tasks_by_type = {row[0]: row[1] for row in type_result.all()}

    return {
        "total_accounts": total_accounts,
        "tasks_by_status": tasks_by_status,
        "tasks_by_type": tasks_by_type,
    }
