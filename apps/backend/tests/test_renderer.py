from __future__ import annotations

import yaml

from app.models.enums import EntrypointType, ProtocolType, TlsMode
from app.services.config_renderer.traefik import (
    PublicationData,
    RenderInput,
    ServiceData,
    find_domain_conflicts,
    render_traefik_dynamic,
)


def _service(slug: str = "grafana") -> ServiceData:
    return ServiceData(
        id="svc-1",
        slug=slug,
        protocol_type=ProtocolType.http,
        backend_host="10.10.0.5",
        backend_port=3000,
        backend_scheme="http",
        enabled=True,
    )


def _web_pub(pub_id: str = "pub-1", domain: str = "grafana.example.com") -> PublicationData:
    return PublicationData(
        id=pub_id,
        service=_service(),
        entrypoint_type=EntrypointType.web,
        domain_or_sni=domain,
        path_prefix=None,
        tls_enabled=True,
        tls_mode=TlsMode.letsencrypt,
        published_port=None,
        public_enabled=True,
        maintenance_mode=False,
        priority=0,
        middleware_profile=None,
    )


def test_render_is_deterministic():
    data = RenderInput(publications=[_web_pub()])
    assert render_traefik_dynamic(data) == render_traefik_dynamic(data)


def test_render_web_router():
    out = render_traefik_dynamic(RenderInput(publications=[_web_pub()]))
    doc = yaml.safe_load(out)
    routers = doc["http"]["routers"]
    name = next(iter(routers))
    assert routers[name]["rule"] == "Host(`grafana.example.com`)"
    assert routers[name]["tls"]["certResolver"] == "letsencrypt"
    assert "websecure" in routers[name]["entryPoints"]
    svc = doc["http"]["services"][name]["loadBalancer"]["servers"][0]["url"]
    assert svc == "http://10.10.0.5:3000"


def test_maintenance_mode_adds_middleware():
    pub = _web_pub()
    pub = PublicationData(**{**pub.__dict__, "maintenance_mode": True})
    out = render_traefik_dynamic(RenderInput(publications=[pub]))
    doc = yaml.safe_load(out)
    name = next(iter(doc["http"]["routers"]))
    assert "cp-maintenance" in doc["http"]["routers"][name]["middlewares"]


def test_disabled_service_is_excluded():
    svc = ServiceData(**{**_service().__dict__, "enabled": False})
    pub = PublicationData(**{**_web_pub().__dict__, "service": svc})
    out = render_traefik_dynamic(RenderInput(publications=[pub]))
    doc = yaml.safe_load(out) or {}
    assert "routers" not in doc.get("http", {})


def test_domain_conflict_detection():
    pubs = [_web_pub("pub-1"), _web_pub("pub-2")]
    conflicts = find_domain_conflicts(RenderInput(publications=pubs))
    assert len(conflicts) == 1
