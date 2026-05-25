from __future__ import annotations

import pytest

from app.services.wgeasy import WgClient, WgEasyClient, get_wgeasy


class FakeWgEasy(WgEasyClient):
    def __init__(self) -> None:
        super().__init__("http://fake")
        self._clients = [
            WgClient(id="c1", name="office", enabled=True, tunnel_ip="10.8.0.2",
                     public_key="PUBKEY1"),
        ]
        self._counter = 1

    async def list_clients(self) -> list[WgClient]:
        return list(self._clients)

    async def create_client(self, name: str) -> WgClient:
        self._counter += 1
        client = WgClient(
            id=f"c{self._counter}", name=name, enabled=True,
            tunnel_ip=f"10.8.0.{self._counter + 1}", public_key=f"PUBKEY{self._counter}",
        )
        self._clients.append(client)
        return client

    async def get_config(self, client_id: str) -> str:
        return f"[Interface]\nPrivateKey = FAKE\nAddress = 10.8.0.x/24\n# {client_id}\n"


@pytest.fixture
def fake_wg(app):
    fake = FakeWgEasy()
    app.dependency_overrides[get_wgeasy] = lambda: fake
    return fake


@pytest.mark.asyncio
async def test_list_wg_clients(client, auth_headers, fake_wg):
    resp = await client.get("/api/v1/published-services/wg-clients", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    names = {c["name"] for c in resp.json()}
    assert "office" in names


@pytest.mark.asyncio
async def test_create_existing_and_toggle(client, auth_headers, fake_wg):
    create = await client.post(
        "/api/v1/published-services",
        headers=auth_headers,
        json={
            "name": "Grafana",
            "domain": "grafana.example.com",
            "protocol_type": "http",
            "backend_port": 3000,
            "wg_mode": "existing",
            "wg_client_id": "c1",
        },
    )
    assert create.status_code == 201, create.text
    body = create.json()
    svc = body["service"]
    assert body["wg_config"] is None  # existing client => no config returned
    assert svc["domain"] == "grafana.example.com"
    assert svc["backend_host"] == "10.8.0.2"  # defaulted to the tunnel IP
    assert svc["wg"]["public_key"] == "PUBKEY1"
    assert svc["proxy_enabled"] is True

    service_id = svc["id"]

    listed = await client.get("/api/v1/published-services", headers=auth_headers)
    assert listed.status_code == 200
    assert any(s["id"] == service_id for s in listed.json())

    off = await client.post(
        f"/api/v1/published-services/{service_id}/toggle?enabled=false",
        headers=auth_headers,
    )
    assert off.status_code == 200
    assert off.json()["proxy_enabled"] is False


@pytest.mark.asyncio
async def test_create_new_returns_config(client, auth_headers, fake_wg):
    create = await client.post(
        "/api/v1/published-services",
        headers=auth_headers,
        json={
            "name": "New Box",
            "domain": "newbox.example.com",
            "protocol_type": "http",
            "backend_host": "127.0.0.1",
            "backend_port": 8080,
            "wg_mode": "new",
            "wg_new_name": "newbox",
        },
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["wg_config"] is not None
    assert body["wg_config_filename"] == "newbox.conf"
    assert body["service"]["backend_host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_update_and_delete(client, auth_headers, fake_wg):
    create = await client.post(
        "/api/v1/published-services",
        headers=auth_headers,
        json={
            "name": "Svc",
            "domain": "svc.example.com",
            "backend_port": 9000,
            "wg_mode": "existing",
            "wg_client_id": "c1",
        },
    )
    service_id = create.json()["service"]["id"]

    patched = await client.patch(
        f"/api/v1/published-services/{service_id}",
        headers=auth_headers,
        json={"backend_port": 9090, "domain": "svc2.example.com"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["backend_port"] == 9090
    assert patched.json()["domain"] == "svc2.example.com"

    deleted = await client.delete(
        f"/api/v1/published-services/{service_id}", headers=auth_headers
    )
    assert deleted.status_code == 200

    missing = await client.get(
        f"/api/v1/published-services/{service_id}", headers=auth_headers
    )
    assert missing.status_code == 404
