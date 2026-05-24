from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select

from app.api.deps import CurrentUserDep, SessionDep, require_superadmin
from app.core.audit import record_audit
from app.core.security import create_access_token, hash_password, verify_password
from app.crud.base import get_or_404, list_paginated
from app.models.enums import Role
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    Token,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.schemas.common import Page

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    session: SessionDep,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    result = await session.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    await record_audit(session, actor=user, action="auth.login", target_type="user",
                       target_id=user.id)
    return Token(access_token=create_access_token(user.id, user.role.value))


@router.post("/login/json", response_model=Token)
async def login_json(session: SessionDep, payload: LoginRequest) -> Token:
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return Token(access_token=create_access_token(user.id, user.role.value))


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUserDep) -> User:
    return current_user


@router.get("/users", response_model=Page[UserRead])
async def list_users(
    session: SessionDep,
    _: Annotated[User, Depends(require_superadmin)],
    limit: int = 50,
    offset: int = 0,
) -> Page[UserRead]:
    items, total = await list_paginated(
        session, User, limit=limit, offset=offset, order_by=User.created_at.desc()
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    session: SessionDep,
    payload: UserCreate,
    actor: Annotated[User, Depends(require_superadmin)],
) -> User:
    exists = await session.execute(
        select(func.count()).select_from(User).where(User.email == payload.email)
    )
    if exists.scalar_one() > 0:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    await session.flush()
    await record_audit(session, actor=actor, action="user.create", target_type="user",
                       target_id=user.id, after={"email": user.email, "role": user.role.value})
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    session: SessionDep,
    user_id: str,
    payload: UserUpdate,
    actor: Annotated[User, Depends(require_superadmin)],
) -> User:
    user = await get_or_404(session, User, user_id)
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        user.hashed_password = hash_password(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    await session.flush()
    await record_audit(session, actor=actor, action="user.update", target_type="user",
                       target_id=user.id)
    return user


def _ensure_roles_exist() -> list[str]:
    return [r.value for r in Role]


@router.get("/roles")
async def list_roles(_: CurrentUserDep) -> list[str]:
    return _ensure_roles_exist()
