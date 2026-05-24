from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_and_me(client, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "admin@test.local"
    assert body["role"] == "superadmin"


@pytest.mark.asyncio
async def test_requires_auth(client):
    resp = await client.get("/api/v1/sites")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_full_publish_flow(client, auth_headers):
    # Create a site
    site_resp = await client.post(
        "/api/v1/sites",
        headers=auth_headers,
        json={"slug": "hq", "name": "Headquarters", "local_subnets": ["192.168.1.0/24"]},
    )
    assert site_resp.status_code == 201, site_resp.text
    site_id = site_resp.json()["id"]

    # Create a service
    svc_resp = await client.post(
        "/api/v1/services",
        headers=auth_headers,
        json={
            "site_id": site_id,
            "name": "Grafana",
            "slug": "grafana",
            "protocol_type": "http",
            "backend_host": "10.0.0.5",
            "backend_port": 3000,
            "exposure_mode": "public",
        },
    )
    assert svc_resp.status_code == 201, svc_resp.text
    service_id = svc_resp.json()["id"]

    # Create a publication
    pub_resp = await client.post(
        "/api/v1/publications",
        headers=auth_headers,
        json={
            "service_id": service_id,
            "entrypoint_type": "web",
            "domain_or_sni": "grafana.example.com",
            "tls_enabled": True,
            "tls_mode": "letsencrypt",
        },
    )
    assert pub_resp.status_code == 201, pub_resp.text

    # Preview the generated config
    preview = await client.get("/api/v1/publications/preview", headers=auth_headers)
    assert preview.status_code == 200
    assert "grafana.example.com" in preview.json()

    # Render and store a revision
    render = await client.post("/api/v1/publications/render", headers=auth_headers)
    assert render.status_code == 200
    assert render.json()["revision"] == 1

    # Audit log captured the actions
    audit = await client.get("/api/v1/audit", headers=auth_headers)
    assert audit.status_code == 200
    actions = {e["action"] for e in audit.json()["items"]}
    assert {"site.create", "service.create", "publication.create"} <= actions


@pytest.mark.asyncio
async def test_peer_keygen(client, auth_headers):
    site = await client.post(
        "/api/v1/sites", headers=auth_headers, json={"slug": "s2", "name": "Site 2"}
    )
    peer = await client.post(
        "/api/v1/peers",
        headers=auth_headers,
        json={"name": "gw", "site_id": site.json()["id"], "assigned_tunnel_ip": "10.10.0.2"},
    )
    peer_id = peer.json()["id"]
    keys = await client.post(f"/api/v1/peers/{peer_id}/rotate-keys", headers=auth_headers)
    assert keys.status_code == 200
    body = keys.json()
    assert body["public_key"] and body["private_key"]
    assert "PrivateKey" in body["config"]

    # The stored peer must expose only the public key.
    fetched = await client.get(f"/api/v1/peers/{peer_id}", headers=auth_headers)
    assert fetched.json()["public_key"] == body["public_key"]


@pytest.mark.asyncio
async def test_provision_gateway(client, auth_headers):
    site = await client.post(
        "/api/v1/sites", headers=auth_headers, json={"slug": "s3", "name": "Site 3"}
    )
    site_id = site.json()["id"]
    resp = await client.post(
        "/api/v1/peers/provision-gateway",
        headers=auth_headers,
        json={"site_id": site_id},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["private_key"] and body["public_key"]
    assert "PrivateKey" in body["config"]
    # An IP from the hub subnet was allocated (.1 is the hub itself).
    assert body["assigned_tunnel_ip"] == "10.10.0.2"

    # The site is now bound to the freshly created gateway peer.
    fetched = await client.get(f"/api/v1/sites/{site_id}", headers=auth_headers)
    assert fetched.json()["gateway_peer_id"] == body["peer_id"]

    # A second gateway gets the next free address.
    site2 = await client.post(
        "/api/v1/sites", headers=auth_headers, json={"slug": "s4", "name": "Site 4"}
    )
    resp2 = await client.post(
        "/api/v1/peers/provision-gateway",
        headers=auth_headers,
        json={"site_id": site2.json()["id"]},
    )
    assert resp2.json()["assigned_tunnel_ip"] == "10.10.0.3"


@pytest.mark.asyncio
async def test_dns_records(client, auth_headers):
    # A valid A record stores value + TTL.
    ok = await client.post(
        "/api/v1/dns",
        headers=auth_headers,
        json={"fqdn": "app.mishteam.site", "record_type": "A",
              "value": "203.0.113.10", "ttl": 3600},
    )
    assert ok.status_code == 201, ok.text
    body = ok.json()
    assert body["value"] == "203.0.113.10"
    assert body["ttl"] == 3600

    # An A record whose value is not an IPv4 address is rejected.
    bad = await client.post(
        "/api/v1/dns",
        headers=auth_headers,
        json={"fqdn": "bad.mishteam.site", "record_type": "A", "value": "not-an-ip"},
    )
    assert bad.status_code == 422

    # A bad TTL is rejected.
    bad_ttl = await client.post(
        "/api/v1/dns",
        headers=auth_headers,
        json={"fqdn": "ttl.mishteam.site", "record_type": "A",
              "value": "203.0.113.11", "ttl": 5},
    )
    assert bad_ttl.status_code == 422

    # A CNAME pointing at a hostname is fine.
    cname = await client.post(
        "/api/v1/dns",
        headers=auth_headers,
        json={"fqdn": "www.mishteam.site", "record_type": "CNAME",
              "value": "app.mishteam.site"},
    )
    assert cname.status_code == 201


@pytest.mark.asyncio
async def test_dashboard(client, auth_headers):
    resp = await client.get("/api/v1/health/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    assert "sites_total" in resp.json()
