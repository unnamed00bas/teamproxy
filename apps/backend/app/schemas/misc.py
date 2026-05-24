from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    AuditResult,
    CertificateStatus,
    ConfigKind,
    DeployMode,
    DeployStatus,
    HealthStatus,
)
from app.schemas.common import ORMModel, TimestampedSchema


# --- Domains --------------------------------------------------------------
class DomainBase(BaseModel):
    fqdn: str
    record_type: str = "A"
    value: str | None = None
    ttl: int | None = None
    active: bool = True
    publication_id: str | None = None


class DomainCreate(DomainBase):
    pass


class DomainUpdate(BaseModel):
    fqdn: str | None = None
    record_type: str | None = None
    value: str | None = None
    ttl: int | None = None
    active: bool | None = None
    publication_id: str | None = None


class DomainRead(TimestampedSchema, DomainBase):
    pass


# --- Certificates ---------------------------------------------------------
class CertificateRead(TimestampedSchema):
    domains: list[str] = Field(default_factory=list)
    status: CertificateStatus
    issuer: str | None
    not_before: datetime | None
    not_after: datetime | None
    last_error: str | None


# --- Deploy revisions -----------------------------------------------------
class DeployRevisionCreate(BaseModel):
    commit_sha: str | None = None
    mode: DeployMode = DeployMode.manual
    summary: str | None = None


class DeployRevisionRead(TimestampedSchema):
    number: int
    commit_sha: str | None
    initiated_by: str | None
    mode: DeployMode
    status: DeployStatus
    summary: str | None
    health_result: HealthStatus
    rollback_available: bool


# --- Audit ----------------------------------------------------------------
class AuditEventRead(ORMModel):
    id: str
    created_at: datetime
    actor_id: str | None
    actor_email: str | None
    action: str
    target_type: str | None
    target_id: str | None
    before: dict | None
    after: dict | None
    result: AuditResult
    deploy_revision_id: str | None


# --- Health ---------------------------------------------------------------
class HealthCheckRead(ORMModel):
    id: str
    target_type: str
    target_id: str
    status: HealthStatus
    detail: str | None
    checked_at: datetime


# --- Generated config -----------------------------------------------------
class GeneratedConfigRead(TimestampedSchema):
    revision: int
    kind: ConfigKind
    checksum: str
    applied: bool
    applied_at: datetime | None
    apply_error: str | None


class GeneratedConfigDetail(GeneratedConfigRead):
    content: str


class ConfigDiff(BaseModel):
    from_revision: int | None
    to_revision: int
    diff: str


class ApplyResult(BaseModel):
    revision: int
    checksum: str
    applied: bool
    error: str | None = None


# --- Dashboard ------------------------------------------------------------
class DashboardStats(BaseModel):
    sites_total: int
    sites_online: int
    sites_offline: int
    peers_total: int
    peers_active: int
    services_total: int
    publications_total: int
    publications_public: int
    broken_routes: int
    expiring_certificates: int
    recent_audit: list[AuditEventRead]
    recent_failed_deploys: list[DeployRevisionRead]


# --- Settings -------------------------------------------------------------
class SecretMetadataRead(TimestampedSchema):
    name: str
    description: str | None
    kind: str | None
    last_rotated_at: datetime | None
