from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import ProtocolType


class WgInfo(BaseModel):
    client_id: str | None = None
    name: str | None = None
    tunnel_ip: str | None = None
    public_key: str | None = None


class WgClientRead(BaseModel):
    id: str
    name: str
    tunnel_ip: str | None = None
    enabled: bool = True


class PublishedServiceRead(BaseModel):
    id: str
    name: str
    domain: str | None = None
    protocol_type: ProtocolType
    backend_host: str
    backend_port: int
    tls_enabled: bool
    proxy_enabled: bool
    enabled: bool
    publication_id: str | None = None
    wg: WgInfo | None = None


class PublishedServiceCreate(BaseModel):
    name: str
    domain: str | None = None
    protocol_type: ProtocolType = ProtocolType.http
    backend_host: str | None = None
    backend_port: int
    tls_enabled: bool = True
    # Either attach an existing wg-easy client or create a fresh one.
    wg_mode: str = Field(pattern="^(existing|new)$")
    wg_client_id: str | None = None
    wg_new_name: str | None = None


class PublishedServiceUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    protocol_type: ProtocolType | None = None
    backend_host: str | None = None
    backend_port: int | None = None
    tls_enabled: bool | None = None
    proxy_enabled: bool | None = None


class PublishedServiceCreateResult(BaseModel):
    service: PublishedServiceRead
    # Present only when a new wg-easy client was created — shown once for download.
    wg_config: str | None = None
    wg_config_filename: str | None = None
