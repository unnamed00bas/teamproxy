from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import EntrypointType, TlsMode


class Publication(UUIDMixin, TimestampMixin, Base):
    """A routing rule that exposes a service through the edge proxy."""

    __tablename__ = "publications"

    service_id: Mapped[str] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    entrypoint_type: Mapped[EntrypointType] = mapped_column(
        Enum(EntrypointType, native_enum=False), default=EntrypointType.web, nullable=False
    )
    domain_or_sni: Mapped[str | None] = mapped_column(String(255), index=True)
    path_prefix: Mapped[str | None] = mapped_column(String(255))
    tls_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tls_mode: Mapped[TlsMode] = mapped_column(
        Enum(TlsMode, native_enum=False), default=TlsMode.letsencrypt, nullable=False
    )
    published_port: Mapped[int | None] = mapped_column(Integer)
    public_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    middleware_profile: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)

    service = relationship("Service", back_populates="publications")
    domains = relationship("Domain", back_populates="publication")
