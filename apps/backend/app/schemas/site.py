from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import SiteStatus
from app.schemas.common import TimestampedSchema


class SiteBase(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    wg_tunnel_subnet: str | None = None
    local_subnets: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SiteCreate(SiteBase):
    slug: str


class SiteUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    status: SiteStatus | None = None
    wg_tunnel_subnet: str | None = None
    local_subnets: list[str] | None = None
    tags: list[str] | None = None
    gateway_peer_id: str | None = None
    agent_version: str | None = None


class SiteRead(TimestampedSchema, SiteBase):
    slug: str
    status: SiteStatus
    gateway_peer_id: str | None
    agent_version: str | None
    last_seen: datetime | None


class SiteSummary(SiteRead):
    nodes_count: int = 0
    services_count: int = 0
    publications_count: int = 0
    peers_count: int = 0
