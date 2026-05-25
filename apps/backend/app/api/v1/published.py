"""Flat 'published service' API.

A single card in the UI = one service exposed to the internet through the edge
proxy over a WireGuard tunnel. This router hides the underlying entities
(Site / Peer / Service / Publication / Domain) behind one resource: each
endpoint composes them so operators never touch the granular models directly.
"""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep, require_operator, require_viewer
from app.core.audit import record_audit
from app.models.domain import Domain
from app.models.enums import EntrypointType, ExposureMode, PeerRole, ProtocolType, TlsMode
from app.models.peer import Peer
from app.models.publication import Publication
from app.models.service import Service
from app.models.site import Site
from app.models.user import User
from app.schemas.common import Message
from app.schemas.published import (
    PublishedServiceCreate,
    PublishedServiceCreateResult,
    PublishedServiceRead,
    PublishedServiceUpdate,
    WgClientRead,
    WgInfo,
)
from app.services.config_renderer import ConfigRenderer
from app.services.wgeasy import WgClient, WgEasyClient, WgEasyError, get_wgeasy

router = APIRouter()

WgEasyDep = Annotated[WgEasyClient, Depends(get_wgeasy)]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "service"


def _entrypoint(protocol: ProtocolType) -> EntrypointType:
    if protocol in (ProtocolType.http, ProtocolType.https):
        return EntrypointType.web
    if protocol == ProtocolType.tcp:
        return EntrypointType.tcp
    return EntrypointType.udp


def _to_read(service: Service) -> PublishedServiceRead:
    pub = service.publications[0] if service.publications else None
    peer = service.peer
    wg = (
        WgInfo(
            client_id=peer.external_ref,
            name=peer.name,
            tunnel_ip=peer.assigned_tunnel_ip,
            public_key=peer.public_key,
        )
        if peer
        else None
    )
    return PublishedServiceRead(
        id=service.id,
        name=service.name,
        domain=pub.domain_or_sni if pub else None,
        protocol_type=service.protocol_type,
        backend_host=service.backend_host,
        backend_port=service.backend_port,
        tls_enabled=pub.tls_enabled if pub else False,
        proxy_enabled=pub.public_enabled if pub else False,
        enabled=service.enabled,
        publication_id=pub.id if pub else None,
        wg=wg,
    )


async def _ensure_default_site(session: SessionDep) -> Site:
    result = await session.execute(select(Site).where(Site.slug == "default"))
    site = result.scalar_one_or_none()
    if site is None:
        site = Site(slug="default", name="Default")
        session.add(site)
        await session.flush()
    return site


async def _upsert_peer(session: SessionDep, site: Site, client: WgClient) -> Peer:
    peer: Peer | None = None
    if client.id:
        result = await session.execute(select(Peer).where(Peer.external_ref == client.id))
        peer = result.scalar_one_or_none()
    if peer is None:
        peer = Peer(name=client.name or "wg", site_id=site.id, role=PeerRole.site_gateway)
        session.add(peer)
    peer.external_ref = client.id
    peer.name = client.name or peer.name
    peer.public_key = client.public_key
    peer.assigned_tunnel_ip = client.tunnel_ip
    peer.enabled = client.enabled
    await session.flush()
    return peer


async def _get_full(session: SessionDep, service_id: str) -> Service:
    result = await session.execute(
        select(Service)
        .where(Service.id == service_id)
        .options(selectinload(Service.publications), selectinload(Service.peer))
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Published service not found")
    return service


@router.get("", response_model=list[PublishedServiceRead])
async def list_published(
    session: SessionDep, _: Annotated[User, Depends(require_viewer)]
) -> list[PublishedServiceRead]:
    result = await session.execute(
        select(Service)
        .options(selectinload(Service.publications), selectinload(Service.peer))
        .order_by(Service.created_at.desc())
    )
    return [_to_read(svc) for svc in result.scalars().all()]


@router.get("/wg-clients", response_model=list[WgClientRead])
async def list_wg_clients(
    wg: WgEasyDep, _: Annotated[User, Depends(require_viewer)]
) -> list[WgClientRead]:
    """List existing wg-easy clients (for the 'choose existing tunnel' step)."""
    try:
        clients = await wg.list_clients()
    except WgEasyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [
        WgClientRead(id=c.id, name=c.name, tunnel_ip=c.tunnel_ip, enabled=c.enabled)
        for c in clients
    ]


@router.post("", response_model=PublishedServiceCreateResult, status_code=201)
async def create_published(
    session: SessionDep,
    payload: PublishedServiceCreate,
    wg: WgEasyDep,
    actor: Annotated[User, Depends(require_operator)],
) -> PublishedServiceCreateResult:
    site = await _ensure_default_site(session)

    wg_config: str | None = None
    wg_filename: str | None = None
    try:
        if payload.wg_mode == "new":
            wg_name = (payload.wg_new_name or payload.name).strip()
            client = await wg.create_client(wg_name)
            wg_config = await wg.get_config(client.id)
            wg_filename = f"{_slugify(wg_name)}.conf"
        else:
            if not payload.wg_client_id:
                raise HTTPException(
                    status_code=422, detail="wg_client_id is required for existing mode"
                )
            client = await wg.get_client(payload.wg_client_id)
    except WgEasyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    peer = await _upsert_peer(session, site, client)

    backend_host = (payload.backend_host or "").strip() or peer.assigned_tunnel_ip
    if not backend_host:
        raise HTTPException(
            status_code=422,
            detail="backend_host is required (selected wg client has no tunnel IP)",
        )

    if payload.domain:
        exists = await session.execute(select(Domain).where(Domain.fqdn == payload.domain))
        if exists.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Domain already in use")

    service = Service(
        site_id=site.id,
        peer_id=peer.id,
        name=payload.name,
        slug=_slugify(payload.name),
        protocol_type=payload.protocol_type,
        backend_host=backend_host,
        backend_port=payload.backend_port,
        exposure_mode=ExposureMode.public,
        enabled=True,
    )
    session.add(service)
    await session.flush()

    pub = Publication(
        service_id=service.id,
        entrypoint_type=_entrypoint(payload.protocol_type),
        domain_or_sni=payload.domain or None,
        tls_enabled=payload.tls_enabled,
        tls_mode=TlsMode.letsencrypt if payload.tls_enabled else TlsMode.off,
        public_enabled=True,
    )
    session.add(pub)
    await session.flush()

    if payload.domain:
        session.add(Domain(fqdn=payload.domain, record_type="A", publication_id=pub.id))
    await session.flush()

    await ConfigRenderer(session).apply()
    await record_audit(
        session, actor=actor, action="published_service.create",
        target_type="service", target_id=service.id,
        after={"name": service.name, "domain": payload.domain},
    )

    full = await _get_full(session, service.id)
    return PublishedServiceCreateResult(
        service=_to_read(full), wg_config=wg_config, wg_config_filename=wg_filename
    )


@router.get("/{service_id}", response_model=PublishedServiceRead)
async def get_published(
    session: SessionDep, service_id: str, _: Annotated[User, Depends(require_viewer)]
) -> PublishedServiceRead:
    return _to_read(await _get_full(session, service_id))


@router.patch("/{service_id}", response_model=PublishedServiceRead)
async def update_published(
    session: SessionDep,
    service_id: str,
    payload: PublishedServiceUpdate,
    actor: Annotated[User, Depends(require_operator)],
) -> PublishedServiceRead:
    service = await _get_full(session, service_id)
    pub = service.publications[0] if service.publications else None

    if payload.name is not None:
        service.name = payload.name
    if payload.backend_host is not None:
        service.backend_host = payload.backend_host.strip()
    if payload.backend_port is not None:
        service.backend_port = payload.backend_port
    if payload.protocol_type is not None:
        service.protocol_type = payload.protocol_type
        if pub:
            pub.entrypoint_type = _entrypoint(payload.protocol_type)

    if pub is not None:
        if payload.domain is not None:
            new_domain = payload.domain or None
            if new_domain and new_domain != pub.domain_or_sni:
                clash = await session.execute(
                    select(Domain).where(Domain.fqdn == new_domain)
                )
                if clash.scalar_one_or_none() is not None:
                    raise HTTPException(status_code=409, detail="Domain already in use")
            pub.domain_or_sni = new_domain
        if payload.tls_enabled is not None:
            pub.tls_enabled = payload.tls_enabled
            pub.tls_mode = TlsMode.letsencrypt if payload.tls_enabled else TlsMode.off
        if payload.proxy_enabled is not None:
            pub.public_enabled = payload.proxy_enabled

    await session.flush()
    await ConfigRenderer(session).apply()
    await record_audit(
        session, actor=actor, action="published_service.update",
        target_type="service", target_id=service.id,
    )
    return _to_read(await _get_full(session, service_id))


@router.post("/{service_id}/toggle", response_model=PublishedServiceRead)
async def toggle_published(
    session: SessionDep,
    service_id: str,
    enabled: bool,
    actor: Annotated[User, Depends(require_operator)],
) -> PublishedServiceRead:
    service = await _get_full(session, service_id)
    if not service.publications:
        raise HTTPException(status_code=400, detail="Service has no publication")
    pub = service.publications[0]
    pub.public_enabled = enabled
    await session.flush()
    await ConfigRenderer(session).apply()
    await record_audit(
        session, actor=actor,
        action="published_service.enable" if enabled else "published_service.disable",
        target_type="service", target_id=service.id,
    )
    return _to_read(await _get_full(session, service_id))


@router.delete("/{service_id}", response_model=Message)
async def delete_published(
    session: SessionDep,
    service_id: str,
    actor: Annotated[User, Depends(require_operator)],
) -> Message:
    service = await _get_full(session, service_id)
    for pub in service.publications:
        rows = await session.execute(select(Domain).where(Domain.publication_id == pub.id))
        for domain in rows.scalars().all():
            await session.delete(domain)
    await session.delete(service)
    await session.flush()
    await ConfigRenderer(session).apply()
    await record_audit(
        session, actor=actor, action="published_service.delete",
        target_type="service", target_id=service_id,
    )
    return Message(detail="Published service deleted")
