"""
Instagram user IDs (commenters) we treat as followers for Comment-to-DM.
When "require follower" is on, only these users get the link; others get the non-follower message.
"""
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at


class InstagramDMAllowedUser(Base):
    """One row per Instagram user ID allowed to receive the link (treated as follower)."""

    __tablename__ = "instagram_dm_allowed_user"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[datetime] = created_at()
