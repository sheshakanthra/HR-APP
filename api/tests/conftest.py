"""Shared pytest fixtures.

Runs against the compose Postgres. Sets a non-placeholder GROQ key so
`validate_secrets()` passes without a real key (no Groq call is made in these
tests). Relies on seeded data; seeds if the DB is empty.
"""

from __future__ import annotations

import os

# Must run before any `app.*` import so cached Settings sees it.
os.environ["GROQ_API_KEY"] = "gsk_test_dummy_key_for_tests"
os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.main import create_app
from app.models.enums import RBACRole
from app.models.user import User

DEMO_PASSWORD = "Passw0rd!"


def _ensure_seed() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(User).limit(1)) is None:
            db.close()
            from app.seed import seed

            seed()
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _seeded() -> None:
    _ensure_seed()


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(create_app())


def _pick_user(role: RBACRole) -> User:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.rbac_role == role).limit(1))
        assert user is not None, f"no seeded user with role {role}"
        return user
    finally:
        db.close()


@pytest.fixture(scope="session")
def creds() -> dict[str, dict[str, str]]:
    """Login credentials for one representative user per role."""
    out: dict[str, dict[str, str]] = {}
    for role in (RBACRole.employee, RBACRole.manager):
        u = _pick_user(role)
        out[role.value] = {"email": u.email, "password": DEMO_PASSWORD}
    out["hr_admin"] = {"email": _pick_user(RBACRole.hr_admin).email, "password": DEMO_PASSWORD}
    out["super_admin"] = {
        "email": settings.seed_admin_email,
        "password": settings.seed_admin_password,
    }
    return out


def _token(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(client: TestClient, creds: dict) -> dict[str, dict[str, str]]:
    return {
        role: {"Authorization": f"Bearer {_token(client, c['email'], c['password'])}"}
        for role, c in creds.items()
    }
