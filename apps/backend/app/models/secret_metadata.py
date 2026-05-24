from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class SecretMetadata(UUIDMixin, TimestampMixin, Base):
    """Metadata about a secret. The actual secret value is never stored here."""

    __tablename__ = "secrets_metadata"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str | None] = mapped_column(String(64))
    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
