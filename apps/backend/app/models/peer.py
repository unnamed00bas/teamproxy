from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import PeerRole, PeerStatus


class Peer(UUIDMixin, TimestampMixin, Base):
    """A WireGuard peer.

    Only public metadata is persisted. Private keys are generated and returned
    once on creation and never stored in plaintext (see secrets handling docs).
    """

    __tablename__ = "peers"

    site_id: Mapped[str | None] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key: Mapped[str | None] = mapped_column(String(64))
    # Reference to a SecretMetadata row if the private key is stored in a vault.
    private_key_ref: Mapped[str | None] = mapped_column(String(255))
    assigned_tunnel_ip: Mapped[str | None] = mapped_column(String(64))
    allowed_ips: Mapped[list[str]] = mapped_column(JSON, default=list)
    endpoint: Mapped[str | None] = mapped_column(String(255))
    persistent_keepalive: Mapped[int | None] = mapped_column(BigInteger)
    role: Mapped[PeerRole] = mapped_column(
        Enum(PeerRole, native_enum=False), default=PeerRole.site_gateway, nullable=False
    )
    status: Mapped[PeerStatus] = mapped_column(
        Enum(PeerStatus, native_enum=False), default=PeerStatus.unknown, nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_handshake: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    transfer_rx: Mapped[int] = mapped_column(BigInteger, default=0)
    transfer_tx: Mapped[int] = mapped_column(BigInteger, default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    site = relationship("Site", back_populates="peers")
