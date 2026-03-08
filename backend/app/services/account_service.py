"""
Instagram account CRUD and connection logic.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instagram_account import InstagramAccount
from app.schemas.account import AccountConnect
from app.core.deps import normalize_id


class AccountService:
    """Create and manage Instagram accounts."""

    @staticmethod
    async def create_account(
        db: AsyncSession,
        user_id: UUID,
        payload: AccountConnect,
    ) -> InstagramAccount:
        """Create a new Instagram account for the user."""
        status = "connected" if (payload.session_cookie and payload.session_cookie.strip()) else "pending"
        account = InstagramAccount(
            user_id=normalize_id(user_id),
            username=payload.username,
            session_cookie=payload.session_cookie,
            proxy_id=normalize_id(payload.proxy_id) if payload.proxy_id else None,
            device_profile=payload.device_profile,
            status=status,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account
