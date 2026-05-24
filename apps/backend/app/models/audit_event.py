from __future__ import annotations

from sqlalchemy import JSON, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AuditResult


class AuditEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_events"

    actor_id: Mapped[str | None] = mapped_column(String(36), index=True)
    actor_email: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(64), index=True)
    target_id: Mapped[str | None] = mapped_column(String(64), index=True)
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)
    result: Mapped[AuditResult] = mapped_column(
        Enum(AuditResult, native_enum=False), default=AuditResult.success, nullable=False
    )
    deploy_revision_id: Mapped[str | None] = mapped_column(String(36))
