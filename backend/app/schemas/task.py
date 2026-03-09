"""Task schemas."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_serializer, model_validator


def _to_utc_iso(d: Optional[datetime]) -> Optional[str]:
    """Serialize datetime as ISO with Z so frontend can show correct local time."""
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.isoformat().replace("+00:00", "Z")


class TaskCreate(BaseModel):
    """Payload to create an automation task."""

    account_id: UUID
    task_type: str  # LIKE_POST, FOLLOW_USER, SEND_DM, COMMENT_POST, UPLOAD_POST
    target: Optional[str] = None  # URL or username
    payload: Optional[dict] = None  # message, caption, etc.
    scheduled_time: Optional[datetime] = None


class BulkFollowCreate(BaseModel):
    """Payload to create follow tasks for all user accounts."""

    target: str  # username to follow (without @)


class BulkLikeCreate(BaseModel):
    """Payload to create like tasks for all user accounts."""

    target: str  # post URL to like


class BulkCommentCreate(BaseModel):
    """Payload to create comment tasks for all user accounts."""

    target: str  # post/reel URL
    message: str  # comment text


class BulkViewReelCreate(BaseModel):
    """Payload to create view-reel tasks for all user accounts (increase reel views)."""

    target: str  # reel URL
    views_per_account: int = 1  # how many view tasks to create per account (1 = one view per account)


class TaskResponse(BaseModel):
    """Task in API responses. Datetimes are serialized as UTC (Z) for correct local display."""

    id: UUID
    account_id: UUID
    account_username: Optional[str] = None  # which account this task is assigned to (for display)
    task_type: str
    target: Optional[str]
    payload: Optional[dict]
    status: str
    result_message: Optional[str] = None  # exact reason for success or failure
    scheduled_time: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _fill_result_message_from_payload(self):
        if self.result_message is None and self.status == "failed" and self.payload and isinstance(self.payload.get("error"), str):
            self.result_message = self.payload["error"]
        return self

    @field_serializer("scheduled_time", "created_at", "completed_at")
    def _serialize_datetime(self, d: Optional[datetime]) -> Optional[str]:
        return _to_utc_iso(d)
