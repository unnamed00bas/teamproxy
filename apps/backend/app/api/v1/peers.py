from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import SessionDep, require_operator, require_viewer
from app.config import settings
from app.core.audit import record_audit
from app.crud.base import apply_updates, get_or_404, list_paginated, snapshot
from app.models.enums import PeerRole, PeerStatus
from app.models.peer import Peer
from app.models.site import Site
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.peer import (
    GatewayProvisionRequest,
    PeerCreate,
    PeerKeygenResult,
    PeerRead,
    PeerUpdate,
)
from app.services.wireguard import (
    allocate_tunnel_ip,
    generate_keypair,
    render_peer_config,
)

router = APIRouter()


def _hub_config_kwargs() -> dict[str, str]:
    """Hub values for config rendering, when configured in settings."""
    kwargs: dict[str, str] = {}
    if settings.wg_hub_public_key:
        kwargs["server_public_key"] = settings.wg_hub_public_key
    if settings.wg_hub_endpoint:
        kwargs["server_endpoint"] = settings.wg_hub_endpoint
    return kwargs


def _hub_configured() -> bool:
    return bool(settings.wg_hub_public_key and settings.wg_hub_endpoint)

_FIELDS = [
    "name", "site_id", "public_key", "assigned_tunnel_ip", "allowed_ips",
    "endpoint", "role", "enabled", "status",
]


@router.get("", response_model=Page[PeerRead])
async def list_peers(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    site_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Page[PeerRead]:
    filters = [Peer.site_id == site_id] if site_id else []
    items, total = await list_paginated(
        session, Peer, limit=limit, offset=offset, filters=filters,
        order_by=Peer.created_at.desc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=PeerRead, status_code=201)
async def create_peer(
    session: SessionDep,
    payload: PeerCreate,
    actor: Annotated[User, Depends(require_operator)],
) -> Peer:
    peer = Peer(**payload.model_dump())
    session.add(peer)
    await session.flush()
    await record_audit(session, actor=actor, action="peer.create", target_type="peer",
                       target_id=peer.id, after=snapshot(peer, _FIELDS))
    return peer


@router.post("/provision-gateway", response_model=PeerKeygenResult, status_code=201)
async def provision_gateway(
    session: SessionDep,
    payload: GatewayProvisionRequest,
    actor: Annotated[User, Depends(require_operator)],
) -> PeerKeygenResult:
    """Create and bind a site gateway peer in one step.

    Allocates the next free tunnel IP from the hub subnet, generates a keypair,
    fills hub public key / endpoint from settings, links the peer to the site
    (``site.gateway_peer_id``), and returns a ready-to-use ``wg-quick`` config.
    The private key is returned once and never stored.
    """
    site = await get_or_404(session, Site, payload.site_id)
    hub_subnet = settings.wg_hub_tunnel_subnet
    used = [
        ip
        for (ip,) in (await session.execute(select(Peer.assigned_tunnel_ip))).all()
        if ip
    ]
    tunnel_ip = allocate_tunnel_ip(hub_subnet, used)

    private_key, public_key = generate_keypair()
    peer = Peer(
        name=payload.name or f"{site.slug}-gateway",
        site_id=site.id,
        role=PeerRole.site_gateway,
        public_key=public_key,
        assigned_tunnel_ip=tunnel_ip,
        allowed_ips=[hub_subnet],
        endpoint=settings.wg_hub_endpoint or None,
        persistent_keepalive=25,
    )
    session.add(peer)
    await session.flush()
    peer.private_key_ref = f"peer:{peer.id}:wg-private"
    site.gateway_peer_id = peer.id
    await session.flush()

    config = render_peer_config(
        private_key=private_key,
        address=f"{tunnel_ip}/32",
        allowed_ips=[hub_subnet],
        **_hub_config_kwargs(),
    )
    await record_audit(session, actor=actor, action="peer.provision_gateway",
                       target_type="peer", target_id=peer.id,
                       after=snapshot(peer, _FIELDS))
    return PeerKeygenResult(
        peer_id=peer.id,
        public_key=public_key,
        private_key=private_key,
        config=config,
        assigned_tunnel_ip=tunnel_ip,
        hub_configured=_hub_configured(),
    )


@router.get("/{peer_id}", response_model=PeerRead)
async def get_peer(
    session: SessionDep, peer_id: str, _: Annotated[User, Depends(require_viewer)]
) -> Peer:
    return await get_or_404(session, Peer, peer_id)


@router.patch("/{peer_id}", response_model=PeerRead)
async def update_peer(
    session: SessionDep,
    peer_id: str,
    payload: PeerUpdate,
    actor: Annotated[User, Depends(require_operator)],
) -> Peer:
    peer = await get_or_404(session, Peer, peer_id)
    before = apply_updates(peer, payload.model_dump(exclude_unset=True))
    await session.flush()
    await record_audit(session, actor=actor, action="peer.update", target_type="peer",
                       target_id=peer.id, before=before)
    return peer


@router.post("/{peer_id}/rotate-keys", response_model=PeerKeygenResult)
async def rotate_keys(
    session: SessionDep, peer_id: str, actor: Annotated[User, Depends(require_operator)]
) -> PeerKeygenResult:
    """Generate a fresh keypair. The private key is returned once, never stored."""
    peer = await get_or_404(session, Peer, peer_id)
    private_key, public_key = generate_keypair()
    peer.public_key = public_key
    peer.private_key_ref = f"peer:{peer.id}:wg-private"
    await session.flush()
    config = render_peer_config(
        private_key=private_key,
        address=peer.assigned_tunnel_ip,
        allowed_ips=peer.allowed_ips,
        **_hub_config_kwargs(),
    )
    await record_audit(session, actor=actor, action="peer.rotate_keys", target_type="peer",
                       target_id=peer.id)
    return PeerKeygenResult(
        peer_id=peer.id, public_key=public_key, private_key=private_key, config=config,
        assigned_tunnel_ip=peer.assigned_tunnel_ip, hub_configured=_hub_configured(),
    )


@router.get("/{peer_id}/config", response_model=Message)
async def peer_config(
    session: SessionDep, peer_id: str, _: Annotated[User, Depends(require_operator)]
) -> Message:
    """Return a config skeleton. The private key is omitted (not stored)."""
    peer = await get_or_404(session, Peer, peer_id)
    config = render_peer_config(
        private_key="<PRIVATE_KEY_NOT_STORED__ROTATE_TO_REGENERATE>",
        address=peer.assigned_tunnel_ip,
        allowed_ips=peer.allowed_ips,
        **_hub_config_kwargs(),
    )
    return Message(detail=config)


@router.post("/{peer_id}/disable", response_model=PeerRead)
async def disable_peer(
    session: SessionDep, peer_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Peer:
    peer = await get_or_404(session, Peer, peer_id)
    peer.enabled = False
    peer.status = PeerStatus.disabled
    await session.flush()
    await record_audit(session, actor=actor, action="peer.disable", target_type="peer",
                       target_id=peer.id)
    return peer


@router.delete("/{peer_id}", response_model=Message)
async def delete_peer(
    session: SessionDep, peer_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Message:
    peer = await get_or_404(session, Peer, peer_id)
    await session.delete(peer)
    await record_audit(session, actor=actor, action="peer.delete", target_type="peer",
                       target_id=peer_id)
    return Message(detail="Peer deleted")
