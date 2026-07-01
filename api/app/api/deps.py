"""Auth + RBAC dependency layer.

`get_current_user` resolves the JWT into a live User. `require_roles` /
`require_min_role` gate routes. Tools and routes both go through these so the
agent can never exceed the caller's permissions.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.enums import RBACRole
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)

# Privilege ranking for "at least this role" checks. Not every capability is
# strictly hierarchical (a manager can approve reports' leave; hr_admin reads
# all records) but privilege level is, which is what require_min_role expresses.
ROLE_RANK: dict[RBACRole, int] = {
    RBACRole.employee: 0,
    RBACRole.manager: 1,
    RBACRole.hr_admin: 2,
    RBACRole.super_admin: 3,
}

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise _CREDENTIALS_EXC
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXC
    if payload.get("type") != "access":
        raise _CREDENTIALS_EXC
    sub = payload.get("sub")
    if sub is None:
        raise _CREDENTIALS_EXC
    user = db.get(User, int(sub))
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


def require_roles(*allowed: RBACRole) -> Callable[..., User]:
    """Gate a route to an explicit set of roles."""
    allowed_set = set(allowed)

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.rbac_role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker


def require_min_role(minimum: RBACRole) -> Callable[..., User]:
    """Gate a route to `minimum` role or higher privilege."""
    threshold = ROLE_RANK[minimum]

    def checker(user: User = Depends(get_current_user)) -> User:
        if ROLE_RANK[user.rbac_role] < threshold:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker


def has_min_role(user: User, minimum: RBACRole) -> bool:
    return ROLE_RANK[user.rbac_role] >= ROLE_RANK[minimum]


def role_in(user: User, roles: Iterable[RBACRole]) -> bool:
    return user.rbac_role in set(roles)
