from __future__ import annotations

from pydantic import BaseModel, EmailStr

from app.models.enums import Role
from app.schemas.common import ORMModel, TimestampedSchema


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: Role = Role.viewer


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = None


class UserRead(TimestampedSchema):
    email: str
    full_name: str | None
    role: Role
    is_active: bool


class CurrentUser(ORMModel):
    id: str
    email: str
    role: Role
