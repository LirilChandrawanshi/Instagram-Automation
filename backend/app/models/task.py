"""
Task model for automation jobs (like, follow, DM, comment, upload).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, created_at, uuid_pk, uuid_fk, json_column


class Task(Base):
    """Automation task tied to an Instagram account."""

    __tablename__ = "tasks"

    # Task type enum values
    LIKE_POST = "LIKE_POST"
    FOLLOW_USER = "FOLLOW_USER"
    SEND_DM = "SEND_DM"
    COMMENT_POST = "COMMENT_POST"
    UPLOAD_POST = "UPLOAD_POST"

    id: Mapped[UUID] = uuid_pk()
    account_id: Mapped[UUID] = uuid_fk(ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=True)  # URL, username, or JSON
    payload: Mapped[Optional[dict]] = json_column(nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, running, completed, failed
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = created_at()
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    account: Mapped["InstagramAccount"] = relationship("InstagramAccount", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task {self.task_type} {self.status}>"
