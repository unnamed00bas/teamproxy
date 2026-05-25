"""Thin async client for the wg-easy HTTP API.

wg-easy is the WireGuard hub and the source of truth for peers. All knowledge
of its (unofficial, session-cookie based) API is isolated here so it can be
adapted in one place if wg-easy changes. Endpoints target the long-standing
wg-easy API surface used by its own web UI:

    POST   /api/session                                {password}
    GET    /api/wireguard/client
    POST   /api/wireguard/client                       {name}
    GET    /api/wireguard/client/{id}/configuration    -> wg-quick text
    POST   /api/wireguard/client/{id}/{enable|disable}
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import settings


class WgEasyError(RuntimeError):
    """Raised when wg-easy is unreachable, unconfigured or returns an error."""


@dataclass
class WgClient:
    id: str
    name: str
    enabled: bool
    tunnel_ip: str | None
    public_key: str | None


class WgEasyClient:
    def __init__(self, base_url: str, password: str = "", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.password = password
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    async def _open(self) -> httpx.AsyncClient:
        if not self.configured:
            raise WgEasyError("wg-easy is not configured (set WGEASY_API_URL)")
        client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        if self.password:
            try:
                resp = await client.post("/api/session", json={"password": self.password})
            except httpx.HTTPError as exc:
                await client.aclose()
                raise WgEasyError(f"cannot reach wg-easy: {exc}") from exc
            if resp.status_code >= 400:
                await client.aclose()
                raise WgEasyError("wg-easy authentication failed")
        return client

    @staticmethod
    def _parse(raw: dict) -> WgClient:
        return WgClient(
            id=str(raw.get("id")),
            name=raw.get("name") or "",
            enabled=bool(raw.get("enabled", True)),
            tunnel_ip=raw.get("address"),
            public_key=raw.get("publicKey"),
        )

    async def list_clients(self) -> list[WgClient]:
        client = await self._open()
        try:
            resp = await client.get("/api/wireguard/client")
            resp.raise_for_status()
            return [self._parse(item) for item in resp.json()]
        except httpx.HTTPError as exc:
            raise WgEasyError(f"failed to list wg-easy clients: {exc}") from exc
        finally:
            await client.aclose()

    async def get_client(self, client_id: str) -> WgClient:
        for client in await self.list_clients():
            if client.id == client_id:
                return client
        raise WgEasyError(f"wg-easy client {client_id} not found")

    async def create_client(self, name: str) -> WgClient:
        client = await self._open()
        try:
            resp = await client.post("/api/wireguard/client", json={"name": name})
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            await client.aclose()
            raise WgEasyError(f"failed to create wg-easy client: {exc}") from exc
        await client.aclose()
        # The create response does not reliably include the new client; locate it
        # by name (newest wins if duplicate names exist).
        matches = [c for c in await self.list_clients() if c.name == name]
        if not matches:
            raise WgEasyError("wg-easy client created but not found in list")
        return matches[-1]

    async def get_config(self, client_id: str) -> str:
        client = await self._open()
        try:
            resp = await client.get(f"/api/wireguard/client/{client_id}/configuration")
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as exc:
            raise WgEasyError(f"failed to fetch wg-easy config: {exc}") from exc
        finally:
            await client.aclose()

    async def set_enabled(self, client_id: str, enabled: bool) -> None:
        action = "enable" if enabled else "disable"
        client = await self._open()
        try:
            resp = await client.post(f"/api/wireguard/client/{client_id}/{action}")
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise WgEasyError(f"failed to {action} wg-easy client: {exc}") from exc
        finally:
            await client.aclose()


def get_wgeasy() -> WgEasyClient:
    """FastAPI dependency: a wg-easy client configured from settings."""
    return WgEasyClient(settings.wgeasy_api_url, settings.wgeasy_password)
