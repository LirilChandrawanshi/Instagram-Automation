"""
FastAPI dependencies: DB session and current user.
"""
from typing import Optional, Union
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


def normalize_id(value: Union[UUID, str]) -> Union[UUID, str]:
    """Convert UUID to str for SQLite; pass-through for PostgreSQL."""
    if get_settings().use_sqlite:
        return str(value)
    if isinstance(value, str):
        return UUID(value)
    return value


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """Resolve JWT to User; raise 401 if missing or invalid."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # SQLite stores id as string(36); PostgreSQL as UUID
    result = await db.execute(select(User).where(User.id == normalize_id(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
