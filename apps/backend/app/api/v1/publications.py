from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import SessionDep, require_operator, require_viewer
from app.core.audit import record_audit
from app.crud.base import apply_updates, get_or_404, list_paginated, snapshot
from app.models.publication import Publication
from app.models.service import Service
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.misc import ApplyResult, ConfigDiff, GeneratedConfigDetail
from app.schemas.publication import (
    PublicationCreate,
    PublicationRead,
    PublicationUpdate,
    RoutePreview,
    SwitchBackendRequest,
)
from app.services.config_renderer import ConfigRenderer

router = APIRouter()

_FIELDS = [
    "service_id", "entrypoint_type", "domain_or_sni", "path_prefix", "tls_enabled",
    "tls_mode", "published_port", "public_enabled", "maintenance_mode", "priority",
    "middleware_profile",
]


@router.get("", response_model=Page[PublicationRead])
async def list_publications(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    service_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Page[PublicationRead]:
    filters = [Publication.service_id == service_id] if service_id else []
    items, total = await list_paginated(
        session, Publication, limit=limit, offset=offset, filters=filters,
        order_by=Publication.priority.asc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=PublicationRead, status_code=201)
async def create_publication(
    session: SessionDep,
    payload: PublicationCreate,
    actor: Annotated[User, Depends(require_operator)],
) -> Publication:
    await get_or_404(session, Service, payload.service_id)
    pub = Publication(**payload.model_dump())
    session.add(pub)
    await session.flush()
    await record_audit(session, actor=actor, action="publication.create",
                       target_type="publication", target_id=pub.id,
                       after=snapshot(pub, _FIELDS))
    return pub


@router.get("/preview", response_model=str)
async def preview_full_config(
    session: SessionDep, _: Annotated[User, Depends(require_viewer)]
) -> str:
    content, _diff, _conflicts = await ConfigRenderer(session).preview()
    return content


@router.get("/conflicts", response_model=list[str])
async def list_conflicts(
    session: SessionDep, _: Annotated[User, Depends(require_viewer)]
) -> list[str]:
    _content, _diff, conflicts = await ConfigRenderer(session).preview()
    return conflicts


@router.post("/render", response_model=GeneratedConfigDetail)
async def render_config(
    session: SessionDep, actor: Annotated[User, Depends(require_operator)]
) -> GeneratedConfigDetail:
    config = await ConfigRenderer(session).render_and_store()
    await record_audit(session, actor=actor, action="config.render",
                       target_type="generated_config", target_id=config.id,
                       after={"revision": config.revision, "checksum": config.checksum})
    return GeneratedConfigDetail.model_validate(config)


@router.post("/apply", response_model=ApplyResult)
async def apply_config(
    session: SessionDep, actor: Annotated[User, Depends(require_operator)]
) -> ApplyResult:
    config = await ConfigRenderer(session).apply()
    await record_audit(session, actor=actor, action="config.apply",
                       target_type="generated_config", target_id=config.id,
                       after={"revision": config.revision, "applied": config.applied,
                              "error": config.apply_error})
    return ApplyResult(
        revision=config.revision, checksum=config.checksum,
        applied=config.applied, error=config.apply_error,
    )


@router.get("/diff", response_model=ConfigDiff)
async def diff_config(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    to_revision: int,
    from_revision: int | None = None,
) -> ConfigDiff:
    try:
        diff = await ConfigRenderer(session).diff_revisions(from_revision, to_revision)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ConfigDiff(from_revision=from_revision, to_revision=to_revision, diff=diff)


@router.post("/rollback/{revision}", response_model=ApplyResult)
async def rollback_config(
    session: SessionDep, revision: int, actor: Annotated[User, Depends(require_operator)]
) -> ApplyResult:
    try:
        config = await ConfigRenderer(session).rollback_to(revision)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await record_audit(session, actor=actor, action="config.rollback",
                       target_type="generated_config", target_id=config.id,
                       after={"rolled_back_to": revision, "new_revision": config.revision})
    return ApplyResult(
        revision=config.revision, checksum=config.checksum,
        applied=config.applied, error=config.apply_error,
    )


@router.get("/{publication_id}", response_model=PublicationRead)
async def get_publication(
    session: SessionDep, publication_id: str, _: Annotated[User, Depends(require_viewer)]
) -> Publication:
    return await get_or_404(session, Publication, publication_id)


@router.patch("/{publication_id}", response_model=PublicationRead)
async def update_publication(
    session: SessionDep,
    publication_id: str,
    payload: PublicationUpdate,
    actor: Annotated[User, Depends(require_operator)],
) -> Publication:
    pub = await get_or_404(session, Publication, publication_id)
    before = apply_updates(pub, payload.model_dump(exclude_unset=True))
    await session.flush()
    await record_audit(session, actor=actor, action="publication.update",
                       target_type="publication", target_id=pub.id, before=before)
    return pub


@router.post("/{publication_id}/toggle", response_model=PublicationRead)
async def toggle_publication(
    session: SessionDep,
    publication_id: str,
    enabled: bool,
    actor: Annotated[User, Depends(require_operator)],
) -> Publication:
    pub = await get_or_404(session, Publication, publication_id)
    pub.public_enabled = enabled
    await session.flush()
    await record_audit(session, actor=actor,
                       action="publication.enable" if enabled else "publication.disable",
                       target_type="publication", target_id=pub.id)
    return pub


@router.post("/{publication_id}/maintenance", response_model=PublicationRead)
async def set_maintenance(
    session: SessionDep,
    publication_id: str,
    enabled: bool,
    actor: Annotated[User, Depends(require_operator)],
) -> Publication:
    pub = await get_or_404(session, Publication, publication_id)
    pub.maintenance_mode = enabled
    await session.flush()
    await record_audit(session, actor=actor, action="publication.maintenance",
                       target_type="publication", target_id=pub.id,
                       after={"maintenance_mode": enabled})
    return pub


@router.post("/{publication_id}/switch-backend", response_model=PublicationRead)
async def switch_backend(
    session: SessionDep,
    publication_id: str,
    payload: SwitchBackendRequest,
    actor: Annotated[User, Depends(require_operator)],
) -> Publication:
    pub = await get_or_404(session, Publication, publication_id)
    await get_or_404(session, Service, payload.service_id)
    before = {"service_id": pub.service_id}
    pub.service_id = payload.service_id
    await session.flush()
    await record_audit(session, actor=actor, action="publication.switch_backend",
                       target_type="publication", target_id=pub.id, before=before,
                       after={"service_id": payload.service_id})
    return pub


@router.get("/{publication_id}/route-preview", response_model=RoutePreview)
async def route_preview(
    session: SessionDep, publication_id: str, _: Annotated[User, Depends(require_viewer)]
) -> RoutePreview:
    await get_or_404(session, Publication, publication_id)
    renderer = ConfigRenderer(session)
    content, _diff, conflicts = await renderer.preview()
    return RoutePreview(publication_id=publication_id, config=content, conflicts=conflicts)


@router.delete("/{publication_id}", response_model=Message)
async def delete_publication(
    session: SessionDep, publication_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Message:
    pub = await get_or_404(session, Publication, publication_id)
    await session.delete(pub)
    await record_audit(session, actor=actor, action="publication.delete",
                       target_type="publication", target_id=publication_id)
    return Message(detail="Publication deleted")
