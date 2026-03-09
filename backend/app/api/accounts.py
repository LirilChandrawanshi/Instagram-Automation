"""
Instagram accounts API: connect, list, delete, check session.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.instagram_account import InstagramAccount
from app.schemas.account import AccountConnect, AccountResponse
from app.core.deps import get_current_user, normalize_id
from app.services.account_service import AccountService
from app.services.automation_service import AutomationService
from app.bot.instagram_client import InstagramClient

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
    # Select only columns needed for response so list works even before migration 002
    stmt = (
        select(
            InstagramAccount.id,
            InstagramAccount.username,
            InstagramAccount.proxy_id,
            InstagramAccount.status,
            InstagramAccount.created_at,
        )
        .where(InstagramAccount.user_id == normalize_id(user.id))
        .order_by(InstagramAccount.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        AccountResponse(
            id=r.id,
            username=r.username,
            proxy_id=r.proxy_id,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rows
    ]


class SessionCheckResponse(BaseModel):
    valid: bool
    message: str


@router.post("/{account_id}/check-session", response_model=SessionCheckResponse)
async def check_session(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionCheckResponse:
    """Check if the account's stored cookies are still valid (logged in to Instagram)."""
    result = await db.execute(
        select(InstagramAccount.id).where(
            InstagramAccount.id == normalize_id(account_id),
            InstagramAccount.user_id == normalize_id(user.id),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    account = await AutomationService._load_account_and_proxy(db, normalize_id(account_id))
    if not account or not getattr(account, "session_cookie", None) or not account.session_cookie.strip():
        return SessionCheckResponse(valid=False, message="No session cookies stored")
    try:
        async with InstagramClient(account) as client:
            valid = await client.ensure_logged_in()
            return SessionCheckResponse(
                valid=valid,
                message="Cookies valid – logged in" if valid else "Session expired or invalid – re-connect with fresh cookies",
            )
    except Exception as e:
        return SessionCheckResponse(valid=False, message=str(e))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete an Instagram account (must belong to current user)."""
    # Verify ownership without loading full model (works before migration 002)
    result = await db.execute(
        select(InstagramAccount.id).where(
            InstagramAccount.id == normalize_id(account_id),
            InstagramAccount.user_id == normalize_id(user.id),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    await db.execute(
        delete(InstagramAccount).where(
            InstagramAccount.id == normalize_id(account_id),
            InstagramAccount.user_id == normalize_id(user.id),
        )
    )
    await db.commit()
