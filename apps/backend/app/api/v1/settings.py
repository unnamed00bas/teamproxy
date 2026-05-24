from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_superadmin, require_viewer
from app.config import settings as app_settings
from app.crud.base import list_paginated
from app.models.secret_metadata import SecretMetadata
from app.models.user import User
from app.schemas.common import Page
from app.schemas.misc import SecretMetadataRead

router = APIRouter()


@router.get("/info")
async def settings_info(_: Annotated[User, Depends(require_viewer)]) -> dict[str, object]:
    """Non-sensitive runtime settings exposed to the UI."""
    return {
        "project_name": app_settings.project_name,
        "environment": app_settings.environment,
        "api_v1_prefix": app_settings.api_v1_prefix,
        "traefik_cert_resolver": app_settings.traefik_cert_resolver,
        "web_entrypoint": app_settings.traefik_web_entrypoint,
        "websecure_entrypoint": app_settings.traefik_websecure_entrypoint,
    }


@router.get("/secrets", response_model=Page[SecretMetadataRead])
async def list_secret_metadata(
    session: SessionDep,
    _: Annotated[User, Depends(require_superadmin)],
    limit: int = 50,
    offset: int = 0,
) -> Page[SecretMetadataRead]:
    """List metadata only. Secret values are never returned by the API."""
    items, total = await list_paginated(
        session, SecretMetadata, limit=limit, offset=offset,
        order_by=SecretMetadata.name.asc(),
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
