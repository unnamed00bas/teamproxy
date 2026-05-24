"""Generic async CRUD helpers shared by routers."""

from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


async def get_or_404(session: AsyncSession, model: type[ModelT], obj_id: str) -> ModelT:
    from fastapi import HTTPException

    obj = await session.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


async def list_paginated(
    session: AsyncSession,
    model: type[ModelT],
    *,
    limit: int = 50,
    offset: int = 0,
    filters: list[Any] | None = None,
    order_by: Any | None = None,
) -> tuple[list[ModelT], int]:
    stmt = select(model)
    count_stmt = select(func.count()).select_from(model)
    for condition in filters or []:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    stmt = stmt.limit(limit).offset(offset)
    items = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar_one()
    return list(items), total


def apply_updates(obj: ModelT, data: dict[str, Any]) -> dict[str, Any]:
    """Apply a partial update dict and return the before-snapshot of changes."""
    before: dict[str, Any] = {}
    for key, value in data.items():
        if hasattr(obj, key):
            before[key] = getattr(obj, key)
            setattr(obj, key, value)
    return before


def snapshot(obj: Base, fields: list[str]) -> dict[str, Any]:
    return {f: _jsonable(getattr(obj, f, None)) for f in fields}


def _jsonable(value: Any) -> Any:
    import enum
    from datetime import datetime

    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value
