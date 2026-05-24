from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_viewer
from app.crud.base import list_paginated
from app.models.audit_event import AuditEvent
from app.models.certificate import Certificate
from app.models.deploy_revision import DeployRevision
from app.models.enums import (
    CertificateStatus,
    DeployStatus,
    HealthStatus,
    PeerStatus,
    SiteStatus,
)
from app.models.health_check import HealthCheck
from app.models.peer import Peer
from app.models.publication import Publication
from app.models.service import Service
from app.models.site import Site
from app.models.user import User
from app.schemas.common import Page
from app.schemas.misc import (
    AuditEventRead,
    DashboardStats,
    DeployRevisionRead,
    HealthCheckRead,
)

router = APIRouter()


async def _count(session: SessionDep, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    for condition in conditions:
        stmt = stmt.where(condition)
    return (await session.execute(stmt)).scalar_one()


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    session: SessionDep, _: Annotated[User, Depends(require_viewer)]
) -> DashboardStats:
    sites_total = await _count(session, Site)
    sites_online = await _count(session, Site, Site.status == SiteStatus.online)
    sites_offline = await _count(session, Site, Site.status == SiteStatus.offline)
    peers_total = await _count(session, Peer)
    peers_active = await _count(session, Peer, Peer.status == PeerStatus.active)
    services_total = await _count(session, Service)
    publications_total = await _count(session, Publication)
    publications_public = await _count(
        session, Publication, Publication.public_enabled.is_(True)
    )

    broken = (
        await session.execute(
            select(func.count())
            .select_from(HealthCheck)
            .where(HealthCheck.status == HealthStatus.red)
        )
    ).scalar_one()

    soon = datetime.now(UTC) + timedelta(days=21)
    expiring = await _count(
        session,
        Certificate,
        Certificate.not_after.is_not(None),
        Certificate.not_after <= soon,
        Certificate.status != CertificateStatus.error,
    )

    recent_audit_rows = (
        await session.execute(
            select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(10)
        )
    ).scalars().all()
    failed_deploys = (
        await session.execute(
            select(DeployRevision)
            .where(DeployRevision.status == DeployStatus.failed)
            .order_by(DeployRevision.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    return DashboardStats(
        sites_total=sites_total,
        sites_online=sites_online,
        sites_offline=sites_offline,
        peers_total=peers_total,
        peers_active=peers_active,
        services_total=services_total,
        publications_total=publications_total,
        publications_public=publications_public,
        broken_routes=broken,
        expiring_certificates=expiring,
        recent_audit=[AuditEventRead.model_validate(a) for a in recent_audit_rows],
        recent_failed_deploys=[
            DeployRevisionRead.model_validate(d) for d in failed_deploys
        ],
    )


@router.get("/checks", response_model=Page[HealthCheckRead])
async def list_checks(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    target_type: str | None = None,
    target_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Page[HealthCheckRead]:
    filters = []
    if target_type:
        filters.append(HealthCheck.target_type == target_type)
    if target_id:
        filters.append(HealthCheck.target_id == target_id)
    items, total = await list_paginated(
        session, HealthCheck, limit=limit, offset=offset, filters=filters,
        order_by=HealthCheck.checked_at.desc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
