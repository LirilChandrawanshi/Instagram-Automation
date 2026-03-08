"""
User model for authentication and ownership of accounts/tasks.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at, uuid_pk


class User(Base):
    """User account; owns Instagram accounts and tasks."""

    __tablename__ = "users"

    id: Mapped[UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = created_at()

    # Relationships
    instagram_accounts: Mapped[list["InstagramAccount"]] = relationship(
        "InstagramAccount", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
