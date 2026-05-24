"""Deterministic Traefik dynamic-configuration renderer.

The control plane owns a slice of Traefik routing through the file provider.
Given the set of enabled publications (and their backing services), this module
produces a single, deterministic YAML document that Traefik watches.

Determinism matters: the same input always yields byte-identical output so that
checksums and diffs between revisions are meaningful. We achieve this by sorting
every collection by a stable key and emitting YAML with ``sort_keys=True``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from app.config import settings
from app.models.enums import EntrypointType, ProtocolType, TlsMode


@dataclass(frozen=True)
class ServiceData:
    id: str
    slug: str
    protocol_type: ProtocolType
    backend_host: str
    backend_port: int
    backend_scheme: str
    enabled: bool


@dataclass(frozen=True)
class PublicationData:
    id: str
    service: ServiceData
    entrypoint_type: EntrypointType
    domain_or_sni: str | None
    path_prefix: str | None
    tls_enabled: bool
    tls_mode: TlsMode
    published_port: int | None
    public_enabled: bool
    maintenance_mode: bool
    priority: int
    middleware_profile: str | None


@dataclass
class RenderInput:
    publications: list[PublicationData] = field(default_factory=list)


def _router_name(pub: PublicationData) -> str:
    return f"cp-{pub.service.slug}-{pub.id[:8]}"


def _backend_url(service: ServiceData) -> str:
    return f"{service.backend_scheme}://{service.backend_host}:{service.backend_port}"


def _web_rule(pub: PublicationData) -> str:
    rule = f"Host(`{pub.domain_or_sni}`)"
    if pub.path_prefix:
        rule += f" && PathPrefix(`{pub.path_prefix}`)"
    return rule


def render_traefik_dynamic(data: RenderInput) -> str:
    """Render the full dynamic config document as YAML text."""
    http_routers: dict[str, Any] = {}
    http_services: dict[str, Any] = {}
    http_middlewares: dict[str, Any] = {}
    tcp_routers: dict[str, Any] = {}
    tcp_services: dict[str, Any] = {}
    udp_routers: dict[str, Any] = {}
    udp_services: dict[str, Any] = {}

    # A shared maintenance middleware returns 503 with a static body.
    http_middlewares["cp-maintenance"] = {
        "errors": {
            "status": ["503"],
            "service": "cp-maintenance-service",
            "query": "/",
        }
    }
    http_services["cp-maintenance-service"] = {
        "loadBalancer": {"servers": [{"url": "http://127.0.0.1:9"}]}
    }

    # Sort for determinism.
    publications = sorted(
        (p for p in data.publications if p.public_enabled and p.service.enabled),
        key=lambda p: (p.priority, p.id),
    )

    for pub in publications:
        name = _router_name(pub)
        svc = pub.service

        if pub.entrypoint_type == EntrypointType.web:
            if not pub.domain_or_sni:
                continue
            router: dict[str, Any] = {
                "rule": _web_rule(pub),
                "service": name,
                "entryPoints": [
                    settings.traefik_websecure_entrypoint
                    if pub.tls_enabled
                    else settings.traefik_web_entrypoint
                ],
                "priority": pub.priority,
            }
            middlewares: list[str] = []
            if pub.middleware_profile:
                middlewares.append(pub.middleware_profile)
            if pub.maintenance_mode:
                middlewares.append("cp-maintenance")
            if middlewares:
                router["middlewares"] = sorted(middlewares)
            if pub.tls_enabled and pub.tls_mode == TlsMode.letsencrypt:
                router["tls"] = {"certResolver": settings.traefik_cert_resolver}
            elif pub.tls_enabled:
                router["tls"] = {}
            http_routers[name] = router
            http_services[name] = {
                "loadBalancer": {"servers": [{"url": _backend_url(svc)}]}
            }

        elif pub.entrypoint_type == EntrypointType.tcp:
            sni = pub.domain_or_sni or "*"
            tcp_routers[name] = {
                "rule": f"HostSNI(`{sni}`)",
                "service": name,
                "entryPoints": [f"tcp-{pub.published_port}"] if pub.published_port else [],
                **(
                    {"tls": {"passthrough": pub.tls_mode == TlsMode.passthrough}}
                    if pub.tls_enabled
                    else {}
                ),
            }
            tcp_services[name] = {
                "loadBalancer": {
                    "servers": [{"address": f"{svc.backend_host}:{svc.backend_port}"}]
                }
            }

        elif pub.entrypoint_type == EntrypointType.udp:
            udp_routers[name] = {
                "service": name,
                "entryPoints": [f"udp-{pub.published_port}"] if pub.published_port else [],
            }
            udp_services[name] = {
                "loadBalancer": {
                    "servers": [{"address": f"{svc.backend_host}:{svc.backend_port}"}]
                }
            }

    document: dict[str, Any] = {}
    http_section: dict[str, Any] = {}
    if http_routers:
        http_section["routers"] = http_routers
    if http_services:
        http_section["services"] = http_services
    if http_middlewares:
        http_section["middlewares"] = http_middlewares
    if http_section:
        document["http"] = http_section

    tcp_section: dict[str, Any] = {}
    if tcp_routers:
        tcp_section["routers"] = tcp_routers
    if tcp_services:
        tcp_section["services"] = tcp_services
    if tcp_section:
        document["tcp"] = tcp_section

    udp_section: dict[str, Any] = {}
    if udp_routers:
        udp_section["routers"] = udp_routers
    if udp_services:
        udp_section["services"] = udp_services
    if udp_section:
        document["udp"] = udp_section

    header = (
        "# Managed by control-plane. Do not edit by hand.\n"
        "# Regenerated deterministically from the service registry.\n"
    )
    body = yaml.safe_dump(document, sort_keys=True, default_flow_style=False)
    return header + body


def find_domain_conflicts(data: RenderInput) -> list[str]:
    """Return human-readable conflict messages for duplicate web domains."""
    seen: dict[tuple[str, str | None], str] = {}
    conflicts: list[str] = []
    for pub in data.publications:
        if pub.entrypoint_type != EntrypointType.web or not pub.domain_or_sni:
            continue
        key = (pub.domain_or_sni, pub.path_prefix)
        if key in seen and seen[key] != pub.id:
            conflicts.append(
                f"Domain {pub.domain_or_sni}{pub.path_prefix or ''} is used by "
                f"multiple publications ({seen[key]}, {pub.id})"
            )
        else:
            seen[key] = pub.id
    return conflicts
