from __future__ import annotations

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import DeployMode, DeployStatus, HealthStatus


class DeployRevision(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "deploy_revisions"

    number: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(64))
    initiated_by: Mapped[str | None] = mapped_column(String(255))
    mode: Mapped[DeployMode] = mapped_column(
        Enum(DeployMode, native_enum=False), default=DeployMode.manual, nullable=False
    )
    status: Mapped[DeployStatus] = mapped_column(
        Enum(DeployStatus, native_enum=False), default=DeployStatus.pending, nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text)
    health_result: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, native_enum=False), default=HealthStatus.unknown, nullable=False
    )
    rollback_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
