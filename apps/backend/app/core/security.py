"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.config import settings

# bcrypt operates on at most 72 bytes; we truncate explicitly so long
# passphrases never raise instead of being silently accepted.
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(pw, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
