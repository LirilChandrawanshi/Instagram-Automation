"""
Tracks comment_id for Comment-to-DM dedup (one Private Reply per comment).
"""
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at


class CommentDMSent(Base):
    """One row per comment_id we already sent a Private Reply to."""

    __tablename__ = "comment_dm_sent"

    comment_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[datetime] = created_at()
