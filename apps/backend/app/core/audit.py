"""Helper for writing audit events.

Every mutating operation should call :func:`record_audit` so the audit log is a
complete, queryable history of who changed what. The event is added to the
current session and committed together with the change it describes.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent
from app.models.enums import AuditResult
from app.models.user import User


async def record_audit(
    session: AsyncSession,
    *,
    actor: User | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    result: AuditResult = AuditResult.success,
    deploy_revision_id: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before=before,
        after=after,
        result=result,
        deploy_revision_id=deploy_revision_id,
    )
    session.add(event)
    await session.flush()
    return event
