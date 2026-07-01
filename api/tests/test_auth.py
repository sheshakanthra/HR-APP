"""Auth + RBAC route tests."""

from __future__ import annotations

from app.api.deps import ROLE_RANK, has_min_role
from app.models.enums import RBACRole
from app.models.user import User


# ---- login ----

def test_login_success(client, creds):
    r = client.post("/auth/login", json=creds["super_admin"])
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["rbac_role"] == "super_admin"
    assert "password_hash" not in body["user"]


def test_login_wrong_password(client, creds):
    bad = {"email": creds["super_admin"]["email"], "password": "wrong-password"}
    r = client.post("/auth/login", json=bad)
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/login", json={"email": "nobody@peopledesk.io", "password": "x"})
    assert r.status_code == 401


# ---- me ----

def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_me_bad_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_me_returns_user_and_employee(client, auth_headers):
    r = client.get("/auth/me", headers=auth_headers["employee"])
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["rbac_role"] == "employee"
    assert body["employee"] is not None
    # profile response must not leak sensitive fields
    assert "password_hash" not in body["user"]


# ---- refresh ----

def test_refresh_flow(client, creds):
    login = client.post("/auth/login", json=creds["employee"]).json()
    r = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_access_token_rejected_as_refresh(client, creds):
    login = client.post("/auth/login", json=creds["employee"]).json()
    r = client.post("/auth/refresh", json={"refresh_token": login["access_token"]})
    assert r.status_code == 401


def test_refresh_token_rejected_as_access(client, creds):
    login = client.post("/auth/login", json=creds["employee"]).json()
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {login['refresh_token']}"})
    assert r.status_code == 401


# ---- RBAC gating on a protected route (audit log = hr_admin+) ----

def test_audit_log_forbidden_for_employee(client, auth_headers):
    assert client.get("/admin/audit-log", headers=auth_headers["employee"]).status_code == 403


def test_audit_log_forbidden_for_manager(client, auth_headers):
    assert client.get("/admin/audit-log", headers=auth_headers["manager"]).status_code == 403


def test_audit_log_allowed_for_hr_admin(client, auth_headers):
    r = client.get("/admin/audit-log", headers=auth_headers["hr_admin"])
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_audit_log_allowed_for_super_admin(client, auth_headers):
    assert client.get("/admin/audit-log", headers=auth_headers["super_admin"]).status_code == 200


def test_audit_log_requires_auth(client):
    assert client.get("/admin/audit-log").status_code == 401


# ---- unit: role ranking logic ----

def _fake(role: RBACRole) -> User:
    u = User()
    u.rbac_role = role
    return u


def test_role_rank_monotonic():
    assert (
        ROLE_RANK[RBACRole.employee]
        < ROLE_RANK[RBACRole.manager]
        < ROLE_RANK[RBACRole.hr_admin]
        < ROLE_RANK[RBACRole.super_admin]
    )


def test_has_min_role():
    assert has_min_role(_fake(RBACRole.hr_admin), RBACRole.manager)
    assert has_min_role(_fake(RBACRole.super_admin), RBACRole.hr_admin)
    assert not has_min_role(_fake(RBACRole.employee), RBACRole.manager)
    assert not has_min_role(_fake(RBACRole.manager), RBACRole.hr_admin)
