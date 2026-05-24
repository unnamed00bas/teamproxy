from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import SessionDep, require_operator, require_viewer
from app.core.audit import record_audit
from app.crud.base import apply_updates, get_or_404, list_paginated, snapshot
from app.models.node import Node
from app.models.service import Service
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.node import NodeCreate, NodeRead, NodeUpdate
from app.schemas.service import ServiceRead

router = APIRouter()

_FIELDS = ["site_id", "hostname", "private_ip", "platform", "is_gateway", "status", "notes"]


@router.get("", response_model=Page[NodeRead])
async def list_nodes(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    site_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Page[NodeRead]:
    filters = [Node.site_id == site_id] if site_id else []
    items, total = await list_paginated(
        session, Node, limit=limit, offset=offset, filters=filters,
        order_by=Node.created_at.desc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=NodeRead, status_code=201)
async def create_node(
    session: SessionDep,
    payload: NodeCreate,
    actor: Annotated[User, Depends(require_operator)],
) -> Node:
    node = Node(**payload.model_dump())
    session.add(node)
    await session.flush()
    await record_audit(session, actor=actor, action="node.create", target_type="node",
                       target_id=node.id, after=snapshot(node, _FIELDS))
    return node


@router.get("/{node_id}", response_model=NodeRead)
async def get_node(
    session: SessionDep, node_id: str, _: Annotated[User, Depends(require_viewer)]
) -> Node:
    return await get_or_404(session, Node, node_id)


@router.patch("/{node_id}", response_model=NodeRead)
async def update_node(
    session: SessionDep,
    node_id: str,
    payload: NodeUpdate,
    actor: Annotated[User, Depends(require_operator)],
) -> Node:
    node = await get_or_404(session, Node, node_id)
    before = apply_updates(node, payload.model_dump(exclude_unset=True))
    await session.flush()
    await record_audit(session, actor=actor, action="node.update", target_type="node",
                       target_id=node.id, before=before)
    return node


@router.get("/{node_id}/services", response_model=list[ServiceRead])
async def node_services(
    session: SessionDep, node_id: str, _: Annotated[User, Depends(require_viewer)]
) -> list[Service]:
    await get_or_404(session, Node, node_id)
    result = await session.execute(select(Service).where(Service.node_id == node_id))
    return list(result.scalars().all())


@router.delete("/{node_id}", response_model=Message)
async def delete_node(
    session: SessionDep, node_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Message:
    node = await get_or_404(session, Node, node_id)
    await session.delete(node)
    await record_audit(session, actor=actor, action="node.delete", target_type="node",
                       target_id=node_id)
    return Message(detail="Node deleted")
