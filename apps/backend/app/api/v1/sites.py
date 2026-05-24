from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_operator, require_viewer
from app.core.audit import record_audit
from app.crud.base import apply_updates, get_or_404, list_paginated, snapshot
from app.models.enums import SiteStatus
from app.models.node import Node
from app.models.peer import Peer
from app.models.publication import Publication
from app.models.service import Service
from app.models.site import Site
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.peer import PeerRead
from app.schemas.site import SiteCreate, SiteRead, SiteSummary, SiteUpdate
from app.services.wireguard import render_gateway_bootstrap

router = APIRouter()

_FIELDS = [
    "slug", "name", "description", "location", "status", "wg_tunnel_subnet",
    "local_subnets", "tags", "gateway_peer_id", "agent_version",
]


async def _summarise(session: SessionDep, site: Site) -> SiteSummary:
    async def _count(model: type, condition) -> int:
        return (
            await session.execute(select(func.count()).select_from(model).where(condition))
        ).scalar_one()

    nodes = await _count(Node, Node.site_id == site.id)
    services = await _count(Service, Service.site_id == site.id)
    peers = await _count(Peer, Peer.site_id == site.id)
    pubs = (
        await session.execute(
            select(func.count())
            .select_from(Publication)
            .join(Service, Service.id == Publication.service_id)
            .where(Service.site_id == site.id)
        )
    ).scalar_one()
    data = SiteRead.model_validate(site).model_dump()
    return SiteSummary(
        **data,
        nodes_count=nodes,
        services_count=services,
        publications_count=pubs,
        peers_count=peers,
    )


@router.get("", response_model=Page[SiteSummary])
async def list_sites(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    limit: int = 50,
    offset: int = 0,
) -> Page[SiteSummary]:
    items, total = await list_paginated(
        session, Site, limit=limit, offset=offset, order_by=Site.created_at.desc()
    )
    summaries = [await _summarise(session, s) for s in items]
    return Page(items=summaries, total=total, limit=limit, offset=offset)


@router.post("", response_model=SiteRead, status_code=201)
async def create_site(
    session: SessionDep,
    payload: SiteCreate,
    actor: Annotated[User, Depends(require_operator)],
) -> Site:
    exists = await session.execute(select(Site).where(Site.slug == payload.slug))
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Site slug already exists")
    site = Site(**payload.model_dump())
    session.add(site)
    await session.flush()
    await record_audit(session, actor=actor, action="site.create", target_type="site",
                       target_id=site.id, after=snapshot(site, _FIELDS))
    return site


@router.get("/{site_id}", response_model=SiteSummary)
async def get_site(
    session: SessionDep, site_id: str, _: Annotated[User, Depends(require_viewer)]
) -> SiteSummary:
    site = await get_or_404(session, Site, site_id)
    return await _summarise(session, site)


@router.patch("/{site_id}", response_model=SiteRead)
async def update_site(
    session: SessionDep,
    site_id: str,
    payload: SiteUpdate,
    actor: Annotated[User, Depends(require_operator)],
) -> Site:
    site = await get_or_404(session, Site, site_id)
    before = apply_updates(site, payload.model_dump(exclude_unset=True))
    await session.flush()
    await record_audit(session, actor=actor, action="site.update", target_type="site",
                       target_id=site.id, before=before, after=snapshot(site, list(before)))
    return site


@router.post("/{site_id}/archive", response_model=SiteRead)
async def archive_site(
    session: SessionDep, site_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Site:
    site = await get_or_404(session, Site, site_id)
    site.status = SiteStatus.archived
    await session.flush()
    await record_audit(session, actor=actor, action="site.archive", target_type="site",
                       target_id=site.id)
    return site


@router.delete("/{site_id}", response_model=Message)
async def delete_site(
    session: SessionDep, site_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Message:
    site = await get_or_404(session, Site, site_id)
    await session.delete(site)
    await record_audit(session, actor=actor, action="site.delete", target_type="site",
                       target_id=site_id)
    return Message(detail="Site deleted")


@router.get("/{site_id}/peers", response_model=list[PeerRead])
async def site_peers(
    session: SessionDep, site_id: str, _: Annotated[User, Depends(require_viewer)]
) -> list[Peer]:
    await get_or_404(session, Site, site_id)
    result = await session.execute(select(Peer).where(Peer.site_id == site_id))
    return list(result.scalars().all())


@router.get("/{site_id}/bootstrap")
async def site_bootstrap(
    session: SessionDep, site_id: str, _: Annotated[User, Depends(require_operator)]
) -> dict[str, str]:
    site = await get_or_404(session, Site, site_id)
    return {"bootstrap": render_gateway_bootstrap(site)}
