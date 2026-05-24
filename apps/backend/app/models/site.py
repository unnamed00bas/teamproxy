from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import SiteStatus


class Site(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sites"

    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[SiteStatus] = mapped_column(
        Enum(SiteStatus, native_enum=False), default=SiteStatus.unknown, nullable=False
    )
    wg_tunnel_subnet: Mapped[str | None] = mapped_column(String(64))
    local_subnets: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    agent_version: Mapped[str | None] = mapped_column(String(64))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # The gateway peer is a Peer with role=site_gateway. Kept as a soft ref to
    # avoid a hard circular FK dependency at bootstrap time.
    gateway_peer_id: Mapped[str | None] = mapped_column(String(36))

    peers = relationship("Peer", back_populates="site", cascade="all, delete-orphan")
    nodes = relationship("Node", back_populates="site", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="site", cascade="all, delete-orphan")
