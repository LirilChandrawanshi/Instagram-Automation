"""
Posts (by media_id) on which Comment-to-DM auto-reply is enabled.
Only comments on these posts get a Private Reply.
"""
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at


class CommentDMEnabledPost(Base):
    """One row per Instagram media (post) ID that has Comment-to-DM enabled."""

    __tablename__ = "comment_dm_enabled_post"

    media_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[datetime] = created_at()
