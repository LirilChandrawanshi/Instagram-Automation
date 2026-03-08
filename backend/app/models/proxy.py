"""
Proxy model for routing Instagram traffic.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid_pk


class Proxy(Base):
    """Proxy server for Instagram requests."""

    __tablename__ = "proxies"

    id: Mapped[UUID] = uuid_pk()
    ip: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length
    port: Mapped[int] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, inactive, error

    # Relationships
    instagram_accounts: Mapped[list["InstagramAccount"]] = relationship(
        "InstagramAccount", back_populates="proxy"
    )

    def __repr__(self) -> str:
        return f"<Proxy {self.ip}:{self.port}>"
