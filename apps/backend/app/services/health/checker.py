"""Backend health probing.

For HTTP services we issue a request to the configured healthcheck path and
compare the status code. For non-HTTP services we attempt a TCP connect. The
result maps to a green/yellow/red status used across the UI.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from app.models.enums import HealthStatus, ProtocolType
from app.models.service import Service


@dataclass
class HealthResult:
    status: HealthStatus
    detail: str


async def _check_tcp(host: str, port: int, timeout: float = 3.0) -> HealthResult:
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001 - best effort close
            pass
        return HealthResult(HealthStatus.green, f"TCP connect to {host}:{port} ok")
    except (TimeoutError, OSError) as exc:
        return HealthResult(HealthStatus.red, f"TCP connect failed: {exc}")


async def _check_http(service: Service, timeout: float = 5.0) -> HealthResult:
    scheme = service.backend_scheme or "http"
    path = service.healthcheck_path or "/"
    url = f"{scheme}://{service.backend_host}:{service.backend_port}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        return HealthResult(HealthStatus.red, f"HTTP request failed: {exc}")
    if response.status_code == service.healthcheck_expected_code:
        return HealthResult(HealthStatus.green, f"HTTP {response.status_code} from {path}")
    return HealthResult(
        HealthStatus.yellow,
        f"HTTP {response.status_code} (expected {service.healthcheck_expected_code})",
    )


async def check_service_health(service: Service) -> HealthResult:
    if not service.enabled:
        return HealthResult(HealthStatus.unknown, "Service disabled")
    if service.protocol_type in (ProtocolType.http, ProtocolType.https):
        return await _check_http(service)
    return await _check_tcp(service.backend_host, service.backend_port)
