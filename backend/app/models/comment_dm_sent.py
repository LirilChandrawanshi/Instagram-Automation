"""
Tracks comment_id for Comment-to-DM dedup (one Private Reply per comment).
Optional comment_text and media_id for dashboard.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at


class CommentDMSent(Base):
    """One row per comment_id we already sent a Private Reply to."""

    __tablename__ = "comment_dm_sent"

    comment_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    comment_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = created_at()
