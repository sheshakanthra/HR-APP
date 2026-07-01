"""Leave balance math + approval state machine tests."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.enums import LeaveStatus
from app.models.leave import LeaveBalance, LeaveRequest
from app.models.user import User
from app.services import leave as leave_svc


# ---- pure function: business day math ----

def test_business_days_single_weekday():
    # a Monday
    d = date(2026, 7, 6)
    assert leave_svc.business_days(d, d) == 1


def test_business_days_full_week_skips_weekend():
    # Mon 2026-07-06 .. Sun 2026-07-12 -> 5 weekdays
    assert leave_svc.business_days(date(2026, 7, 6), date(2026, 7, 12)) == 5


def test_business_days_end_before_start_raises():
    with pytest.raises(leave_svc.LeaveValidationError):
        leave_svc.business_days(date(2026, 7, 10), date(2026, 7, 1))


# ---- helper: find a manager + one of their reports from seed ----

def _manager_with_report():
    db = SessionLocal()
    try:
        report = db.scalar(select(Employee).where(Employee.manager_id.isnot(None)).limit(1))
        manager = db.get(Employee, report.manager_id)
        mgr_user = db.scalar(select(User).where(User.employee_id == manager.id))
        rep_user = db.scalar(select(User).where(User.employee_id == report.id))
        return {
            "manager_email": mgr_user.email,
            "report_email": rep_user.email,
            "report_id": report.id,
        }
    finally:
        db.close()


def _headers(client, email, password="Passw0rd!"):
    tok = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


# ---- API: balance + full request lifecycle ----

def test_balance_endpoint(client, auth_headers):
    r = client.get("/leave/balance", headers=auth_headers["employee"])
    assert r.status_code == 200
    balances = r.json()
    assert len(balances) >= 1
    for b in balances:
        assert b["available"] == pytest.approx(b["accrued"] - b["used"])


def test_submit_then_approve_flow(client):
    ctx = _manager_with_report()
    rep_h = _headers(client, ctx["report_email"])
    mgr_h = _headers(client, ctx["manager_email"])

    types = client.get("/leave/types", headers=rep_h).json()
    annual = next(t for t in types if t["code"] == "ANNUAL")

    start = date.today() + timedelta(days=10)
    while start.weekday() >= 5:
        start += timedelta(days=1)
    end = start  # one business day

    bal_before = client.get("/leave/balance", headers=rep_h).json()
    used_before = next(b["used"] for b in bal_before if b["leave_type_id"] == annual["id"])

    create = client.post(
        "/leave/requests",
        headers=rep_h,
        json={
            "leave_type_id": annual["id"],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "reason": "vacation",
        },
    )
    assert create.status_code == 201, create.text
    req = create.json()
    assert req["status"] == "pending"
    assert req["days"] == 1

    # hold applied
    bal_after = client.get("/leave/balance", headers=rep_h).json()
    used_after = next(b["used"] for b in bal_after if b["leave_type_id"] == annual["id"])
    assert used_after == pytest.approx(used_before + 1)

    # appears in manager's queue
    queue = client.get("/leave/approvals", headers=mgr_h).json()
    assert any(q["id"] == req["id"] for q in queue)

    # approve
    ok = client.post(f"/leave/requests/{req['id']}/approve", headers=mgr_h, json={"note": "ok"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "approved"

    # balance hold remains after approval (approved days stay counted)
    bal_final = client.get("/leave/balance", headers=rep_h).json()
    used_final = next(b["used"] for b in bal_final if b["leave_type_id"] == annual["id"])
    assert used_final == pytest.approx(used_before + 1)


def test_reject_releases_hold(client):
    ctx = _manager_with_report()
    rep_h = _headers(client, ctx["report_email"])
    mgr_h = _headers(client, ctx["manager_email"])
    annual = next(
        t for t in client.get("/leave/types", headers=rep_h).json() if t["code"] == "SICK"
    )

    start = date.today() + timedelta(days=20)
    while start.weekday() >= 5:
        start += timedelta(days=1)

    used_before = next(
        b["used"] for b in client.get("/leave/balance", headers=rep_h).json()
        if b["leave_type_id"] == annual["id"]
    )
    req = client.post(
        "/leave/requests",
        headers=rep_h,
        json={"leave_type_id": annual["id"], "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "x"},
    ).json()

    client.post(f"/leave/requests/{req['id']}/reject", headers=mgr_h, json={"note": "no"})
    used_after = next(
        b["used"] for b in client.get("/leave/balance", headers=rep_h).json()
        if b["leave_type_id"] == annual["id"]
    )
    assert used_after == pytest.approx(used_before)


def test_cannot_approve_already_decided(client):
    ctx = _manager_with_report()
    rep_h = _headers(client, ctx["report_email"])
    mgr_h = _headers(client, ctx["manager_email"])
    annual = next(
        t for t in client.get("/leave/types", headers=rep_h).json() if t["code"] == "CASUAL"
    )
    start = date.today() + timedelta(days=30)
    while start.weekday() >= 5:
        start += timedelta(days=1)
    req = client.post(
        "/leave/requests",
        headers=rep_h,
        json={"leave_type_id": annual["id"], "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "x"},
    ).json()
    client.post(f"/leave/requests/{req['id']}/approve", headers=mgr_h, json={})
    # second decision must fail (illegal transition)
    again = client.post(f"/leave/requests/{req['id']}/reject", headers=mgr_h, json={})
    assert again.status_code == 400


def test_employee_cannot_approve(client, auth_headers):
    # employees lack the manager role entirely
    r = client.get("/leave/approvals", headers=auth_headers["employee"])
    assert r.status_code == 403


def test_manager_cannot_approve_non_report(client):
    """A plain manager must not decide a request from someone who isn't their report."""
    from app.models.enums import RBACRole

    db = SessionLocal()
    try:
        # Pick a user whose role is EXACTLY manager (not hr_admin/super_admin,
        # which are legitimately allowed to decide any request).
        mgr_user = db.scalar(
            select(User).where(User.rbac_role == RBACRole.manager).limit(1)
        )
        mgr_a_id = mgr_user.employee_id
        # A report belonging to a DIFFERENT manager.
        report_of_b = db.scalar(
            select(Employee).where(
                Employee.manager_id.isnot(None), Employee.manager_id != mgr_a_id
            ).limit(1)
        )
        mgr_a_email = mgr_user.email
        report_b_email = db.scalar(
            select(User).where(User.employee_id == report_of_b.id)
        ).email
    finally:
        db.close()

    rep_h = _headers(client, report_b_email)
    mgr_a_h = _headers(client, mgr_a_email)
    annual = next(t for t in client.get("/leave/types", headers=rep_h).json() if t["code"] == "ANNUAL")
    start = date.today() + timedelta(days=40)
    while start.weekday() >= 5:
        start += timedelta(days=1)
    req = client.post(
        "/leave/requests",
        headers=rep_h,
        json={"leave_type_id": annual["id"], "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "x"},
    ).json()
    # manager A tries to approve manager B's report -> 403
    resp = client.post(f"/leave/requests/{req['id']}/approve", headers=mgr_a_h, json={})
    assert resp.status_code == 403
    # cleanup: cancel as owner
    client.post(f"/leave/requests/{req['id']}/cancel", headers=rep_h)
