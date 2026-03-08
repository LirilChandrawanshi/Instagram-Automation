"""Instagram account and proxy schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AccountConnect(BaseModel):
    """Payload to connect an Instagram account."""

    username: str
    session_cookie: Optional[str] = None
    proxy_id: Optional[UUID] = None
    device_profile: Optional[dict] = None


class AccountResponse(BaseModel):
    """Instagram account in API responses."""

    id: UUID
    username: str
    proxy_id: Optional[UUID]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProxyResponse(BaseModel):
    """Proxy in API responses (no password)."""

    id: UUID
    ip: str
    port: int
    username: Optional[str]
    status: str

    model_config = {"from_attributes": True}
