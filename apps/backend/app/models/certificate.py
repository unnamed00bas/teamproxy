from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import CertificateStatus


class Certificate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "certificates"

    domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[CertificateStatus] = mapped_column(
        Enum(CertificateStatus, native_enum=False),
        default=CertificateStatus.pending,
        nullable=False,
    )
    issuer: Mapped[str | None] = mapped_column(String(255))
    not_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    not_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
