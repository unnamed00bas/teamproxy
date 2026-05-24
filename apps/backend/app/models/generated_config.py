from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ConfigKind


class GeneratedConfig(UUIDMixin, TimestampMixin, Base):
    """A rendered reverse-proxy configuration revision.

    Every render is stored so we can diff revisions and roll back. The content
    is the full deterministic output for the given ``kind``.
    """

    __tablename__ = "generated_configs"

    revision: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    kind: Mapped[ConfigKind] = mapped_column(
        Enum(ConfigKind, native_enum=False),
        default=ConfigKind.traefik_dynamic,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    apply_error: Mapped[str | None] = mapped_column(Text)
