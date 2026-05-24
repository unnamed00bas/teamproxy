from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import NodeStatus


class Node(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "nodes"

    site_id: Mapped[str] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    private_ip: Mapped[str | None] = mapped_column(String(64))
    platform: Mapped[str | None] = mapped_column(String(128))
    is_gateway: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[NodeStatus] = mapped_column(
        Enum(NodeStatus, native_enum=False), default=NodeStatus.unknown, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    site = relationship("Site", back_populates="nodes")
    services = relationship("Service", back_populates="node")
