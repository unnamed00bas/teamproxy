"""Enumerations shared across ORM models and Pydantic schemas."""

from __future__ import annotations

import enum


class Role(str, enum.Enum):
    superadmin = "superadmin"
    operator = "operator"
    viewer = "viewer"


class SiteStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    degraded = "degraded"
    disabled = "disabled"
    archived = "archived"
    unknown = "unknown"


class PeerRole(str, enum.Enum):
    site_gateway = "site_gateway"
    admin = "admin"


class PeerStatus(str, enum.Enum):
    active = "active"
    stale = "stale"
    disabled = "disabled"
    unknown = "unknown"


class NodeStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    unknown = "unknown"


class ProtocolType(str, enum.Enum):
    http = "http"
    https = "https"
    tcp = "tcp"
    udp = "udp"


class ExposureMode(str, enum.Enum):
    public = "public"
    private = "private"
    disabled = "disabled"


class EntrypointType(str, enum.Enum):
    web = "web"
    tcp = "tcp"
    udp = "udp"


class TlsMode(str, enum.Enum):
    off = "off"
    letsencrypt = "letsencrypt"
    passthrough = "passthrough"
    custom = "custom"


class CertificateStatus(str, enum.Enum):
    ok = "ok"
    pending = "pending"
    error = "error"


class DeployMode(str, enum.Enum):
    auto = "auto"
    manual = "manual"


class DeployStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    rolled_back = "rolled_back"


class HealthStatus(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"
    unknown = "unknown"


class AuditResult(str, enum.Enum):
    success = "success"
    failure = "failure"


class ConfigKind(str, enum.Enum):
    traefik_dynamic = "traefik_dynamic"
