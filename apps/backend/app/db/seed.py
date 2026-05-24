"""Idempotent bootstrap seed: create the first superadmin if no users exist."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.models.enums import Role
from app.models.user import User

logger = logging.getLogger(__name__)


async def ensure_first_superadmin(session: AsyncSession) -> None:
    count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    if count > 0:
        return
    user = User(
        email=settings.first_superadmin_email,
        full_name="Initial Superadmin",
        role=Role.superadmin,
        hashed_password=hash_password(settings.first_superadmin_password),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    logger.info("Created initial superadmin: %s", settings.first_superadmin_email)
