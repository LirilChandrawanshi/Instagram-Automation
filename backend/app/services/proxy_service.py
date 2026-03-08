"""
Proxy CRUD and optional validation.
"""
from uuid import UUID

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proxy import Proxy


class ProxyService:
    """Manage proxy records."""

    @staticmethod
    async def get_by_id(db: AsyncSession, proxy_id: UUID) -> Optional[Proxy]:
        """Return proxy by id."""
        result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
        return result.scalar_one_or_none()
