"""
Instagram accounts API: connect, list, delete.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.instagram_account import InstagramAccount
from app.schemas.account import AccountConnect, AccountResponse
from app.core.deps import get_current_user, normalize_id
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/connect", response_model=AccountResponse)
async def connect_account(
    payload: AccountConnect,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AccountResponse:
    """Connect a new Instagram account for the current user."""
    account = await AccountService.create_account(db, user.id, payload)
    return AccountResponse.model_validate(account)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AccountResponse]:
    """List all Instagram accounts for the current user."""
    result = await db.execute(
        select(InstagramAccount).where(InstagramAccount.user_id == normalize_id(user.id))
    )
    accounts = result.scalars().all()
    return [AccountResponse.model_validate(a) for a in accounts]


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete an Instagram account (must belong to current user)."""
    result = await db.execute(
        select(InstagramAccount).where(
            InstagramAccount.id == normalize_id(account_id),
            InstagramAccount.user_id == normalize_id(user.id),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    await db.delete(account)
    await db.commit()
