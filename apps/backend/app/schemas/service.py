from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import ExposureMode, ProtocolType
from app.schemas.common import TimestampedSchema


class ServiceBase(BaseModel):
    site_id: str
    node_id: str | None = None
    name: str
    slug: str
    description: str | None = None
    protocol_type: ProtocolType = ProtocolType.http
    backend_host: str
    backend_port: int
    backend_scheme: str = "http"
    healthcheck_path: str | None = "/"
    healthcheck_expected_code: int = 200
    owner: str | None = None
    exposure_mode: ExposureMode = ExposureMode.private
    tags: list[str] = Field(default_factory=list)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    site_id: str | None = None
    node_id: str | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    protocol_type: ProtocolType | None = None
    backend_host: str | None = None
    backend_port: int | None = None
    backend_scheme: str | None = None
    healthcheck_path: str | None = None
    healthcheck_expected_code: int | None = None
    owner: str | None = None
    enabled: bool | None = None
    exposure_mode: ExposureMode | None = None
    tags: list[str] | None = None


class ServiceRead(TimestampedSchema, ServiceBase):
    enabled: bool
