from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Domain(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "domains"

    fqdn: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    record_type: Mapped[str] = mapped_column(String(16), default="A")
    value: Mapped[str | None] = mapped_column(String(255))
    ttl: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    publication_id: Mapped[str | None] = mapped_column(
        ForeignKey("publications.id", ondelete="SET NULL")
    )

    publication = relationship("Publication", back_populates="domains")
