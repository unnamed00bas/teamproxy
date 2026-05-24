from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin
from app.models.enums import HealthStatus


class HealthCheck(UUIDMixin, Base):
    __tablename__ = "health_checks"

    target_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, native_enum=False), default=HealthStatus.unknown, nullable=False
    )
    detail: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
