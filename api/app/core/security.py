"""Password hashing (Argon2) and JWT helpers.

JWT encode/decode is used from Milestone 2 onward; hashing is used by seed.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_ph = PasswordHasher()


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:  # noqa: BLE001 - malformed hash etc.
        return False


def _create_token(subject: str, expires_delta: timedelta, token_type: str, claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, claims: dict | None = None) -> str:
    return _create_token(
        subject,
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
        claims,
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
