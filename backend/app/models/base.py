"""
Declarative base and common columns for all models.
Works with both PostgreSQL and SQLite (USE_SQLITE=1).
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _use_sqlite() -> bool:
    try:
        from app.config import get_settings
        return get_settings().use_sqlite
    except Exception:
        return False


def uuid_pk() -> Mapped[uuid.UUID]:
    """UUID primary key column (String(36) for SQLite, UUID for PostgreSQL)."""
    if _use_sqlite():
        return mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def uuid_fk(*args, **kwargs):
    """UUID foreign key column (String(36) for SQLite, UUID for PostgreSQL)."""
    if _use_sqlite():
        return mapped_column(String(36), *args, **kwargs)
    return mapped_column(PG_UUID(as_uuid=True), *args, **kwargs)


def json_column(nullable: bool = False):
    """JSON/JSONB column (JSON for SQLite, JSONB for PostgreSQL)."""
    if _use_sqlite():
        from sqlalchemy import JSON
        return mapped_column(JSON, nullable=nullable)
    return mapped_column(JSONB, nullable=nullable)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


def created_at() -> Mapped[datetime]:
    """Created at timestamp."""
    return mapped_column(DateTime(timezone=True), server_default=func.now())
