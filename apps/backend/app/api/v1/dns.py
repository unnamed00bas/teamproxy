from __future__ import annotations

import ipaddress
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import SessionDep, require_operator, require_viewer
from app.core.audit import record_audit
from app.crud.base import apply_updates, get_or_404, list_paginated
from app.models.domain import Domain
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.misc import DomainCreate, DomainRead, DomainUpdate

router = APIRouter()


def _validate_record(record_type: str, value: str | None, ttl: int | None) -> None:
    """Reject records whose value does not match the type, or bad TTLs.

    Validation only runs when a value is supplied — an empty value is allowed
    so a record can be registered before its target is known.
    """
    if ttl is not None and not (60 <= ttl <= 2_592_000):
        raise HTTPException(status_code=422, detail="TTL must be between 60 and 2592000 seconds")
    if not value:
        return
    rtype = record_type.upper()
    if rtype == "A":
        try:
            ipaddress.IPv4Address(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail="A record value must be an IPv4 address"
            ) from exc
    elif rtype == "AAAA":
        try:
            ipaddress.IPv6Address(value)
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail="AAAA record value must be an IPv6 address"
            ) from exc
    elif rtype == "CNAME" and (" " in value or "/" in value):
        raise HTTPException(status_code=422, detail="CNAME value must be a hostname")


@router.get("", response_model=Page[DomainRead])
async def list_domains(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    limit: int = 50,
    offset: int = 0,
) -> Page[DomainRead]:
    items, total = await list_paginated(
        session, Domain, limit=limit, offset=offset, order_by=Domain.fqdn.asc()
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=DomainRead, status_code=201)
async def create_domain(
    session: SessionDep,
    payload: DomainCreate,
    actor: Annotated[User, Depends(require_operator)],
) -> Domain:
    _validate_record(payload.record_type, payload.value, payload.ttl)
    exists = await session.execute(select(Domain).where(Domain.fqdn == payload.fqdn))
    if exists.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Domain already exists")
    domain = Domain(**payload.model_dump())
    session.add(domain)
    await session.flush()
    await record_audit(session, actor=actor, action="domain.create", target_type="domain",
                       target_id=domain.id, after={"fqdn": domain.fqdn})
    return domain


@router.patch("/{domain_id}", response_model=DomainRead)
async def update_domain(
    session: SessionDep,
    domain_id: str,
    payload: DomainUpdate,
    actor: Annotated[User, Depends(require_operator)],
) -> Domain:
    domain = await get_or_404(session, Domain, domain_id)
    fields = payload.model_dump(exclude_unset=True)
    _validate_record(
        fields.get("record_type", domain.record_type),
        fields.get("value", domain.value),
        fields.get("ttl", domain.ttl),
    )
    before = apply_updates(domain, fields)
    await session.flush()
    await record_audit(session, actor=actor, action="domain.update", target_type="domain",
                       target_id=domain.id, before=before)
    return domain


@router.delete("/{domain_id}", response_model=Message)
async def delete_domain(
    session: SessionDep, domain_id: str, actor: Annotated[User, Depends(require_operator)]
) -> Message:
    domain = await get_or_404(session, Domain, domain_id)
    await session.delete(domain)
    await record_audit(session, actor=actor, action="domain.delete", target_type="domain",
                       target_id=domain_id)
    return Message(detail="Domain deleted")
