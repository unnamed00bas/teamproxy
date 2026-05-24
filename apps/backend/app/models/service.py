from __future__ import annotations

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ExposureMode, ProtocolType


class Service(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "services"

    site_id: Mapped[str] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[str | None] = mapped_column(ForeignKey("nodes.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    protocol_type: Mapped[ProtocolType] = mapped_column(
        Enum(ProtocolType, native_enum=False), default=ProtocolType.http, nullable=False
    )
    backend_host: Mapped[str] = mapped_column(String(255), nullable=False)
    backend_port: Mapped[int] = mapped_column(Integer, nullable=False)
    backend_scheme: Mapped[str] = mapped_column(String(16), default="http")
    healthcheck_path: Mapped[str | None] = mapped_column(String(255), default="/")
    healthcheck_expected_code: Mapped[int] = mapped_column(Integer, default=200)
    owner: Mapped[str | None] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    exposure_mode: Mapped[ExposureMode] = mapped_column(
        Enum(ExposureMode, native_enum=False), default=ExposureMode.private, nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    site = relationship("Site", back_populates="services")
    node = relationship("Node", back_populates="services")
    publications = relationship(
        "Publication", back_populates="service", cascade="all, delete-orphan"
    )
