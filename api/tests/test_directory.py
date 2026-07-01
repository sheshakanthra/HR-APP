"""Directory search, profile RBAC scoping, and org chart tests."""

from __future__ import annotations

from sqlalchemy import select

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.user import User


def _headers(client, email, password="Passw0rd!"):
    tok = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_search_requires_auth(client):
    assert client.get("/directory/employees").status_code == 401


def test_search_and_pagination(client, auth_headers):
    r = client.get("/directory/employees?page=1&page_size=10", headers=auth_headers["employee"])
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 200
    assert len(body["items"]) == 10
    # card must not leak sensitive fields
    for item in body["items"]:
        assert "hire_date" not in item
        assert "employment_status" not in item


def test_org_chart_has_single_root(client, auth_headers):
    r = client.get("/directory/org-chart", headers=auth_headers["super_admin"])
    assert r.status_code == 200
    tree = r.json()
    assert len(tree) == 1  # only the CEO has no manager
    assert len(tree[0]["reports"]) >= 1


def test_profile_self_visible(client):
    db = SessionLocal()
    try:
        emp = db.scalar(select(Employee).where(Employee.manager_id.isnot(None)).limit(1))
        user = db.scalar(select(User).where(User.employee_id == emp.id))
        email, emp_id = user.email, emp.id
    finally:
        db.close()
    h = _headers(client, email)
    r = client.get(f"/directory/employees/{emp_id}", headers=h)
    assert r.status_code == 200
    assert "hire_date" in r.json()  # extended fields visible for self


def test_profile_extended_forbidden_for_stranger(client, auth_headers):
    """An employee cannot see another (non-report) person's full record."""
    # A = the seeded plain-employee fixture user (has no reports, not hr_admin).
    me = client.get("/auth/me", headers=auth_headers["employee"]).json()
    a_emp_id = me["employee"]["id"]
    db = SessionLocal()
    try:
        b = db.scalar(select(Employee).where(Employee.id != a_emp_id).limit(1))
        b_id = b.id
    finally:
        db.close()
    h = auth_headers["employee"]
    # extended profile -> 403
    assert client.get(f"/directory/employees/{b_id}", headers=h).status_code == 403
    # but the contact card is allowed
    card = client.get(f"/directory/employees/{b_id}/card", headers=h)
    assert card.status_code == 200
    assert "work_email" in card.json()


def test_hr_admin_can_view_any_profile(client, auth_headers):
    db = SessionLocal()
    try:
        emp = db.scalar(select(Employee).where(Employee.manager_id.isnot(None)).limit(1))
        emp_id = emp.id
    finally:
        db.close()
    r = client.get(f"/directory/employees/{emp_id}", headers=auth_headers["hr_admin"])
    assert r.status_code == 200
    assert "employment_status" in r.json()
