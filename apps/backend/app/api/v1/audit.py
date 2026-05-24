from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_viewer
from app.crud.base import list_paginated
from app.models.audit_event import AuditEvent
from app.models.user import User
from app.schemas.common import Page
from app.schemas.misc import AuditEventRead

router = APIRouter()


@router.get("", response_model=Page[AuditEventRead])
async def list_audit(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    actor_id: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Page[AuditEventRead]:
    filters = []
    if actor_id:
        filters.append(AuditEvent.actor_id == actor_id)
    if action:
        filters.append(AuditEvent.action == action)
    if target_type:
        filters.append(AuditEvent.target_type == target_type)
    if target_id:
        filters.append(AuditEvent.target_id == target_id)
    if since:
        filters.append(AuditEvent.created_at >= since)
    if until:
        filters.append(AuditEvent.created_at <= until)
    items, total = await list_paginated(
        session, AuditEvent, limit=limit, offset=offset, filters=filters,
        order_by=AuditEvent.created_at.desc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
