"""Shared FastAPI dependencies: DB session, authentication and RBAC."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rbac import role_satisfies
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.enums import Role
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login", auto_error=True
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise credentials_exc from exc
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exc
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exc
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[AsyncSession, Depends(get_db)]


def require_role(
    minimum: Role,
) -> Callable[[User], Coroutine[Any, Any, User]]:
    async def _dependency(user: CurrentUserDep) -> User:
        if not role_satisfies(user.role, minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{minimum.value}' or higher",
            )
        return user

    return _dependency


require_viewer = require_role(Role.viewer)
require_operator = require_role(Role.operator)
require_superadmin = require_role(Role.superadmin)
