"""
Instagram account CRUD and connection logic.
"""
import json
import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.instagram_account import InstagramAccount
from app.schemas.account import AccountConnect
from app.core.deps import normalize_id
from app.bot.device_fingerprint import generate_device_profile


class AccountService:
    """Create and manage Instagram accounts."""

    @staticmethod
    async def create_account(
        db: AsyncSession,
        user_id: UUID,
        payload: AccountConnect,
    ) -> InstagramAccount:
        """Create a new Instagram account. Generates device fingerprint if not provided."""
        status = "connected" if (payload.session_cookie and payload.session_cookie.strip()) else "pending"
        device_profile = payload.device_profile
        if device_profile is None:
            device_profile = generate_device_profile()
        now = datetime.now(timezone.utc)
        user_id_norm = normalize_id(user_id)
        proxy_id_norm = normalize_id(payload.proxy_id) if payload.proxy_id else None

        try:
            account = InstagramAccount(
                user_id=user_id_norm,
                username=payload.username,
                session_cookie=payload.session_cookie,
                proxy_id=proxy_id_norm,
                device_profile=device_profile,
                status=status,
                connected_at=now if status == "connected" else None,
            )
            db.add(account)
            await db.commit()
            await db.refresh(account)
            return account
        except DatabaseError as e:
            orig = getattr(e, "orig", e)
            err = (str(orig) + " " + str(e)).lower()
            if "no such column" in err or "has no column" in err or "unknown column" in err or ("column" in err and "does not exist" in err):
                await db.rollback()
                account_id = str(uuid.uuid4()) if get_settings().use_sqlite else uuid.uuid4()
                user_id_str = str(user_id_norm)
                proxy_id_str = str(proxy_id_norm) if proxy_id_norm is not None else None
                device_profile_str = json.dumps(device_profile) if isinstance(device_profile, dict) else (device_profile or "null")
                await db.execute(
                    text(
                        "INSERT INTO instagram_accounts (id, user_id, username, session_cookie, proxy_id, device_profile, status) "
                        "VALUES (:id, :user_id, :username, :session_cookie, :proxy_id, :device_profile, :status)"
                    ),
                    {
                        "id": account_id,
                        "user_id": user_id_str,
                        "username": payload.username,
                        "session_cookie": payload.session_cookie,
                        "proxy_id": proxy_id_str,
                        "device_profile": device_profile_str,
                        "status": status,
                    },
                )
                await db.commit()
                result = await db.execute(
                    select(
                        InstagramAccount.id,
                        InstagramAccount.username,
                        InstagramAccount.proxy_id,
                        InstagramAccount.status,
                        InstagramAccount.created_at,
                    ).where(InstagramAccount.id == account_id)
                )
                row = result.one()
                out = type("AccountRow", (), {})()
                out.id = row.id
                out.username = row.username
                out.proxy_id = row.proxy_id
                out.status = row.status
                # Ensure datetime for Pydantic (SQLite may return str)
                out.created_at = row.created_at
                if isinstance(out.created_at, str):
                    try:
                        out.created_at = datetime.fromisoformat(out.created_at.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        out.created_at = datetime.now(timezone.utc)
                return out
            raise
