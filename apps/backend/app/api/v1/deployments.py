from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import SessionDep, require_operator, require_viewer
from app.core.audit import record_audit
from app.crud.base import get_or_404, list_paginated
from app.models.deploy_revision import DeployRevision
from app.models.enums import DeployStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.misc import DeployRevisionCreate, DeployRevisionRead

router = APIRouter()


@router.get("", response_model=Page[DeployRevisionRead])
async def list_deployments(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    limit: int = 50,
    offset: int = 0,
) -> Page[DeployRevisionRead]:
    items, total = await list_paginated(
        session, DeployRevision, limit=limit, offset=offset,
        order_by=DeployRevision.number.desc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=DeployRevisionRead, status_code=201)
async def record_deployment(
    session: SessionDep,
    payload: DeployRevisionCreate,
    actor: Annotated[User, Depends(require_operator)],
) -> DeployRevision:
    """Register a new deploy revision. Called by the CD pipeline or manually."""
    last = (
        await session.execute(
            select(DeployRevision.number).order_by(DeployRevision.number.desc()).limit(1)
        )
    ).scalar_one_or_none()
    revision = DeployRevision(
        number=(last or 0) + 1,
        commit_sha=payload.commit_sha,
        mode=payload.mode,
        summary=payload.summary,
        initiated_by=actor.email,
        status=DeployStatus.running,
        rollback_available=(last or 0) > 0,
    )
    session.add(revision)
    await session.flush()
    await record_audit(session, actor=actor, action="deploy.start",
                       target_type="deploy_revision", target_id=revision.id,
                       after={"number": revision.number, "commit": revision.commit_sha})
    return revision


@router.patch("/{revision_id}", response_model=DeployRevisionRead)
async def update_deployment(
    session: SessionDep,
    revision_id: str,
    status: DeployStatus,
    actor: Annotated[User, Depends(require_operator)],
) -> DeployRevision:
    revision = await get_or_404(session, DeployRevision, revision_id)
    revision.status = status
    await session.flush()
    await record_audit(session, actor=actor, action="deploy.update",
                       target_type="deploy_revision", target_id=revision.id,
                       deploy_revision_id=revision.id, after={"status": status.value})
    return revision
