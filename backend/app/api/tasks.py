"""
Tasks API: create, list, delete automation tasks.
"""
import random
from datetime import datetime, timedelta, timezone
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
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    BulkFollowCreate,
    BulkLikeCreate,
    BulkCommentCreate,
    BulkViewReelCreate,
)
from app.core.deps import get_current_user, normalize_id
from app.services.scheduler_service import SchedulerService
from app.utils.rate_limiter import can_perform_action
from app.config import get_testing_mode

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
    # Ensure account belongs to user (select only id so this works before migration 002)
    result = await db.execute(
        select(InstagramAccount.id).where(
            InstagramAccount.id == normalize_id(payload.account_id),
            InstagramAccount.user_id == normalize_id(user.id),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    task = await SchedulerService.create_and_enqueue(db, payload)
    return TaskResponse.model_validate(task)


@router.post("/bulk-follow", response_model=list[TaskResponse])
async def bulk_follow(
    payload: BulkFollowCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """Create one FOLLOW_USER task per account (for target username). Tasks are spread over next 24h."""
    # Select only id so this works even if migration 002 (new columns) has not been run
    result = await db.execute(
        select(InstagramAccount.id).where(InstagramAccount.user_id == normalize_id(user.id))
    )
    account_ids = [row[0] for row in result.all()]
    if not account_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accounts found")
    target = payload.target.strip().lstrip("@")
    if not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target username required")
    created = []
    now = datetime.now(timezone.utc)
    for account_id in account_ids:
        if not await can_perform_action(db, account_id, Task.FOLLOW_USER):
            continue
        delta_sec = random.randint(0, 24 * 3600)
        scheduled_time = now + timedelta(seconds=delta_sec)
        task_create = TaskCreate(
            account_id=account_id,
            task_type=Task.FOLLOW_USER,
            target=target,
            scheduled_time=scheduled_time,
        )
        task = await SchedulerService.create_and_enqueue(db, task_create)
        created.append(task)
    return [TaskResponse.model_validate(t) for t in created]


@router.post("/bulk-like", response_model=list[TaskResponse])
async def bulk_like(
    payload: BulkLikeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """Create one LIKE_POST task per account for the given post URL.

    Testing mode ON  → all tasks fire instantly (no scheduling spread).
    Testing mode OFF → tasks spread over 24h to reduce detection risk.
    """
    result = await db.execute(
        select(InstagramAccount.id).where(InstagramAccount.user_id == normalize_id(user.id))
    )
    account_ids = [row[0] for row in result.all()]
    if not account_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accounts found")
    target = payload.target.strip()
    if not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post URL required")
    testing = get_testing_mode()
    created = []
    now = datetime.now(timezone.utc)
    for account_id in account_ids:
        if not testing and not await can_perform_action(db, account_id, Task.LIKE_POST):
            continue
        scheduled_time = None if testing else now + timedelta(seconds=random.randint(0, 24 * 3600))
        task_create = TaskCreate(
            account_id=account_id,
            task_type=Task.LIKE_POST,
            target=target,
            scheduled_time=scheduled_time,
        )
        task = await SchedulerService.create_and_enqueue(db, task_create)
        created.append(task)
    return [TaskResponse.model_validate(t) for t in created]


@router.post("/bulk-comment", response_model=list[TaskResponse])
async def bulk_comment(
    payload: BulkCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """Create one COMMENT_POST task per account for the given post/reel URL and message."""
    result = await db.execute(
        select(InstagramAccount.id).where(InstagramAccount.user_id == normalize_id(user.id))
    )
    account_ids = [row[0] for row in result.all()]
    if not account_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accounts found")
    target = payload.target.strip()
    message = (payload.message or "").strip()
    if not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post/reel URL required")
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment message required")
    testing = get_testing_mode()
    created = []
    now = datetime.now(timezone.utc)
    for account_id in account_ids:
        if not testing and not await can_perform_action(db, account_id, Task.COMMENT_POST):
            continue
        delta_sec = 0 if testing else random.randint(0, 24 * 3600)
        scheduled_time = None if testing else now + timedelta(seconds=delta_sec)
        task_create = TaskCreate(
            account_id=account_id,
            task_type=Task.COMMENT_POST,
            target=target,
            payload={"message": message},
            scheduled_time=scheduled_time,
        )
        task = await SchedulerService.create_and_enqueue(db, task_create)
        created.append(task)
    return [TaskResponse.model_validate(t) for t in created]


@router.post("/bulk-view-reel", response_model=list[TaskResponse])
async def bulk_view_reel(
    payload: BulkViewReelCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """Create VIEW_REEL tasks per account for the given reel URL. views_per_account = how many views per account."""
    result = await db.execute(
        select(InstagramAccount.id).where(InstagramAccount.user_id == normalize_id(user.id))
    )
    account_ids = [row[0] for row in result.all()]
    if not account_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accounts found")
    target = payload.target.strip()
    if not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reel URL required")
    views_per = max(1, min(500, payload.views_per_account))
    testing = get_testing_mode()
    created = []
    now = datetime.now(timezone.utc)
    for account_id in account_ids:
        for i in range(views_per):
            if not testing and not await can_perform_action(db, account_id, Task.VIEW_REEL):
                break
            delta_sec = 0 if testing else random.randint(0, 24 * 3600) + (i * 60)
            scheduled_time = None if testing else now + timedelta(seconds=delta_sec)
            task_create = TaskCreate(
                account_id=account_id,
                task_type=Task.VIEW_REEL,
                target=target,
                scheduled_time=scheduled_time,
            )
            task = await SchedulerService.create_and_enqueue(db, task_create)
            created.append(task)
    return [TaskResponse.model_validate(t) for t in created]


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    account_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """List tasks for the current user's accounts. Includes account_username (which account the task is assigned to)."""
    query = (
        select(Task)
        .join(InstagramAccount)
        .where(InstagramAccount.user_id == normalize_id(user.id))
    )
    if account_id is not None:
        query = query.where(Task.account_id == normalize_id(account_id))
    if status_filter:
        query = query.where(Task.status == status_filter)
    query = query.order_by(Task.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    account_ids = list({t.account_id for t in tasks})
    username_map = {}
    if account_ids:
        acc_result = await db.execute(
            select(InstagramAccount.id, InstagramAccount.username).where(InstagramAccount.id.in_(account_ids))
        )
        for row in acc_result.all():
            username_map[str(row.id)] = row.username
    out = []
    for t in tasks:
        account_username = username_map.get(str(t.account_id))
        resp = TaskResponse.model_validate(t)
        out.append(resp.model_copy(update={"account_username": account_username}))
    return out


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
