from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import EntrypointType, TlsMode
from app.schemas.common import TimestampedSchema


class PublicationBase(BaseModel):
    service_id: str
    entrypoint_type: EntrypointType = EntrypointType.web
    domain_or_sni: str | None = None
    path_prefix: str | None = None
    tls_enabled: bool = True
    tls_mode: TlsMode = TlsMode.letsencrypt
    published_port: int | None = None
    public_enabled: bool = True
    maintenance_mode: bool = False
    priority: int = 0
    middleware_profile: str | None = None
    notes: str | None = None


class PublicationCreate(PublicationBase):
    pass


class PublicationUpdate(BaseModel):
    service_id: str | None = None
    entrypoint_type: EntrypointType | None = None
    domain_or_sni: str | None = None
    path_prefix: str | None = None
    tls_enabled: bool | None = None
    tls_mode: TlsMode | None = None
    published_port: int | None = None
    public_enabled: bool | None = None
    maintenance_mode: bool | None = None
    priority: int | None = None
    middleware_profile: str | None = None
    notes: str | None = None


class PublicationRead(TimestampedSchema, PublicationBase):
    pass


class SwitchBackendRequest(BaseModel):
    service_id: str


class RoutePreview(BaseModel):
    publication_id: str
    config: str
    conflicts: list[str] = []
