from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_operator, require_viewer
from app.core.audit import record_audit
from app.crud.base import apply_updates, get_or_404, list_paginated, snapshot
from app.models.health_check import HealthCheck
from app.models.service import Service
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.misc import HealthCheckRead
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate
from app.services.health import check_service_health

router = APIRouter()

_FIELDS = [
    "site_id", "node_id", "name", "slug", "protocol_type", "backend_host",
    "backend_port", "backend_scheme", "exposure_mode", "enabled",
]


@router.get("", response_model=Page[ServiceRead])
async def list_services(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    site_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Page[ServiceRead]:
    filters = [Service.site_id == site_id] if site_id else []
    items, total = await list_paginated(
        session, Service, limit=limit, offset=offset, filters=filters,
        order_by=Service.created_at.desc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=ServiceRead, status_code=201)
async def create_service(
    session: SessionDep,
    payload: ServiceCreate,
    actor: Annotated[User, Depends(require_operator)],
) -> Service:
    service = Service(**payload.model_dump())
    session.add(service)
    await session.flush()
    await record_audit(session, actor=actor, action="service.create", target_type="service",
                       target_id=service.id, after=snapshot(service, _FIELDS))
    return service


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(
    session: SessionDep, service_id: str, _: Annotated[User, Depends(require_viewer)]
) -> Service:
    return await get_or_404(session, Service, service_id)


@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(
    session: SessionDep,
    service_id: str,
    payload: ServiceUpdate,
    actor: Annotated[User, Depends(require_operator)],
) -> Service:
    service = await get_or_404(session, Service, service_id)
    before = apply_updates(service, payload.model_dump(exclude_unset=True))
    await session.flush()
    await record_audit(session, actor=actor, action="service.update", target_type="service",
                       target_id=service.id, before=before)
    return service


@router.post("/{service_id}/clone", response_model=ServiceRead, status_code=201)
async def clone_service(
    session: SessionDep, service_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Service:
    source = await get_or_404(session, Service, service_id)
    data = snapshot(source, [
        "site_id", "node_id", "name", "protocol_type", "backend_host", "backend_port",
        "backend_scheme", "healthcheck_path", "healthcheck_expected_code", "owner",
        "exposure_mode", "tags", "description",
    ])
    clone = Service(**data, slug=f"{source.slug}-copy", enabled=False)
    session.add(clone)
    await session.flush()
    await record_audit(session, actor=actor, action="service.clone", target_type="service",
                       target_id=clone.id, before={"source": source.id})
    return clone


@router.delete("/{service_id}", response_model=Message)
async def delete_service(
    session: SessionDep, service_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Message:
    service = await get_or_404(session, Service, service_id)
    await session.delete(service)
    await record_audit(session, actor=actor, action="service.delete", target_type="service",
                       target_id=service_id)
    return Message(detail="Service deleted")


@router.post("/{service_id}/check", response_model=HealthCheckRead)
async def run_health_check(
    session: SessionDep, service_id: str, _: Annotated[User, Depends(require_viewer)]
) -> HealthCheck:
    service = await get_or_404(session, Service, service_id)
    result = await check_service_health(service)
    check = HealthCheck(
        target_type="service", target_id=service.id,
        status=result.status, detail=result.detail,
    )
    session.add(check)
    await session.flush()
    return check
