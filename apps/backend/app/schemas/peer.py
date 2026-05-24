from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PeerRole, PeerStatus
from app.schemas.common import TimestampedSchema


class PeerBase(BaseModel):
    name: str
    site_id: str | None = None
    public_key: str | None = None
    assigned_tunnel_ip: str | None = None
    allowed_ips: list[str] = Field(default_factory=list)
    endpoint: str | None = None
    persistent_keepalive: int | None = None
    role: PeerRole = PeerRole.site_gateway
    notes: str | None = None


class PeerCreate(PeerBase):
    pass


class PeerUpdate(BaseModel):
    name: str | None = None
    site_id: str | None = None
    public_key: str | None = None
    assigned_tunnel_ip: str | None = None
    allowed_ips: list[str] | None = None
    endpoint: str | None = None
    persistent_keepalive: int | None = None
    role: PeerRole | None = None
    enabled: bool | None = None
    notes: str | None = None


class PeerRead(TimestampedSchema, PeerBase):
    status: PeerStatus
    enabled: bool
    last_handshake: datetime | None
    transfer_rx: int
    transfer_tx: int


class GatewayProvisionRequest(BaseModel):
    """One-click provisioning of a site gateway peer."""

    site_id: str
    name: str | None = None


class PeerKeygenResult(BaseModel):
    """Returned once when keys are generated. Private key is not persisted."""

    peer_id: str
    public_key: str
    private_key: str
    config: str
    assigned_tunnel_ip: str | None = None
    hub_configured: bool = True
