"""
Tasks API: create, list, delete automation tasks.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.instagram_account import InstagramAccount
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse
from app.core.deps import get_current_user, normalize_id
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _ensure_account_owned_by_user(db: AsyncSession, account_id: UUID, user_id: UUID) -> Optional[InstagramAccount]:
    """Return InstagramAccount if it belongs to user."""
    # We'll check in the service or here
    return None  # placeholder; actual check in create


@router.post("/create", response_model=TaskResponse)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskResponse:
    """Create an automation task and enqueue it to Celery."""
    # Ensure account belongs to user
    result = await db.execute(
        select(InstagramAccount).where(
            InstagramAccount.id == normalize_id(payload.account_id),
            InstagramAccount.user_id == normalize_id(user.id),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    task = await SchedulerService.create_and_enqueue(db, payload)
    return TaskResponse.model_validate(task)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    account_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """List tasks for the current user's accounts."""
    query = select(Task).join(InstagramAccount).where(InstagramAccount.user_id == normalize_id(user.id))
    if account_id is not None:
        query = query.where(Task.account_id == normalize_id(account_id))
    if status_filter:
        query = query.where(Task.status == status_filter)
    query = query.order_by(Task.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete a task (must belong to user via account)."""
    result = await db.execute(
        select(Task)
        .join(InstagramAccount)
        .where(Task.id == normalize_id(task_id), InstagramAccount.user_id == normalize_id(user.id))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    await db.delete(task)
    await db.commit()
