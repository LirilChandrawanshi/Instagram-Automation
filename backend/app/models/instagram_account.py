"""
Instagram account linked to a user; holds session and device profile.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at, uuid_pk, uuid_fk, json_column


class InstagramAccount(Base):
    """Connected Instagram account with session and optional proxy."""

    __tablename__ = "instagram_accounts"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = uuid_fk(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    session_cookie: Mapped[str] = mapped_column(Text, nullable=True)  # Store serialized cookies/state
    proxy_id: Mapped[Optional[UUID]] = uuid_fk(ForeignKey("proxies.id", ondelete="SET NULL"), nullable=True)
    device_profile: Mapped[Optional[dict]] = json_column(nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # connected, pending, error
    created_at: Mapped[datetime] = created_at()
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    action_block_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="instagram_accounts")
    proxy: Mapped[Optional["Proxy"]] = relationship("Proxy", back_populates="instagram_accounts")
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InstagramAccount {self.username}>"
