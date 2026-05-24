from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_viewer
from app.crud.base import list_paginated
from app.models.certificate import Certificate
from app.models.user import User
from app.schemas.common import Page
from app.schemas.misc import CertificateRead

router = APIRouter()


@router.get("", response_model=Page[CertificateRead])
async def list_certificates(
    session: SessionDep,
    _: Annotated[User, Depends(require_viewer)],
    limit: int = 50,
    offset: int = 0,
) -> Page[CertificateRead]:
    items, total = await list_paginated(
        session, Certificate, limit=limit, offset=offset,
        order_by=Certificate.not_after.asc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
