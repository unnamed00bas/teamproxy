"""Background jobs: health sweeps, peer staleness and config rendering."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.session import SessionFactory
from app.models.enums import HealthStatus, PeerStatus, SiteStatus
from app.models.health_check import HealthCheck
from app.models.peer import Peer
from app.models.service import Service
from app.models.site import Site
from app.services.config_renderer import ConfigRenderer
from app.services.health import check_service_health
from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)

STALE_HANDSHAKE_AFTER = timedelta(minutes=5)


@celery.task(name="app.tasks.jobs.sweep_service_health")
def sweep_service_health() -> dict[str, int]:
    return asyncio.run(_sweep_service_health())


async def _sweep_service_health() -> dict[str, int]:
    checked = 0
    red = 0
    async with SessionFactory() as session:
        services = (
            await session.execute(select(Service).where(Service.enabled.is_(True)))
        ).scalars().all()
        for service in services:
            result = await check_service_health(service)
            session.add(
                HealthCheck(
                    target_type="service",
                    target_id=service.id,
                    status=result.status,
                    detail=result.detail,
                )
            )
            checked += 1
            if result.status == HealthStatus.red:
                red += 1
        await session.commit()
    logger.info("Health sweep complete: %d checked, %d red", checked, red)
    return {"checked": checked, "red": red}


@celery.task(name="app.tasks.jobs.sweep_peer_staleness")
def sweep_peer_staleness() -> dict[str, int]:
    return asyncio.run(_sweep_peer_staleness())


async def _sweep_peer_staleness() -> dict[str, int]:
    now = datetime.now(UTC)
    stale = 0
    async with SessionFactory() as session:
        peers = (
            await session.execute(select(Peer).where(Peer.enabled.is_(True)))
        ).scalars().all()
        for peer in peers:
            if peer.last_handshake is None:
                peer.status = PeerStatus.unknown
                continue
            last = peer.last_handshake
            if last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            if now - last > STALE_HANDSHAKE_AFTER:
                peer.status = PeerStatus.stale
                stale += 1
            else:
                peer.status = PeerStatus.active
        # Roll site status up from gateway peer freshness.
        sites = (await session.execute(select(Site))).scalars().all()
        for site in sites:
            site_peers = [p for p in peers if p.site_id == site.id]
            if not site_peers:
                continue
            if any(p.status == PeerStatus.active for p in site_peers):
                site.status = SiteStatus.online
            elif all(p.status == PeerStatus.stale for p in site_peers):
                site.status = SiteStatus.degraded
        await session.commit()
    logger.info("Peer staleness sweep: %d stale", stale)
    return {"stale": stale}


@celery.task(name="app.tasks.jobs.render_config_revision")
def render_config_revision() -> dict[str, object]:
    return asyncio.run(_render_config_revision())


async def _render_config_revision() -> dict[str, object]:
    async with SessionFactory() as session:
        config = await ConfigRenderer(session).render_and_store()
        await session.commit()
        return {"revision": config.revision, "checksum": config.checksum}
