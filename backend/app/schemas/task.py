"""Task schemas."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_serializer


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


class TaskResponse(BaseModel):
    """Task in API responses. Datetimes are serialized as UTC (Z) for correct local display."""

    id: UUID
    account_id: UUID
    task_type: str
    target: Optional[str]
    payload: Optional[dict]
    status: str
    scheduled_time: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_serializer("scheduled_time", "created_at", "completed_at")
    def _serialize_datetime(self, d: Optional[datetime]) -> Optional[str]:
        return _to_utc_iso(d)
