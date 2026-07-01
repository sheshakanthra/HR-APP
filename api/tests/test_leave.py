"""Leave balance math + approval state machine tests.

Lifecycle tests use an ISOLATED team (fresh employees + large balances created
per run) so they don't deplete shared seeded balances and stay deterministic.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.department import Department
from app.models.employee import Employee
from app.models.enums import LeaveStatus, RBACRole
from app.models.leave import LeaveBalance, LeaveRequest, LeaveType
from app.models.user import User
from app.services import leave as leave_svc

PW = "Passw0rd!"


# ---- pure function: business day math ----

def test_business_days_single_weekday():
    assert leave_svc.business_days(date(2026, 7, 6), date(2026, 7, 6)) == 1  # a Monday


def test_business_days_full_week_skips_weekend():
    # Mon 2026-07-06 .. Sun 2026-07-12 -> 5 weekdays
    assert leave_svc.business_days(date(2026, 7, 6), date(2026, 7, 12)) == 5


def test_business_days_end_before_start_raises():
    with pytest.raises(leave_svc.LeaveValidationError):
        leave_svc.business_days(date(2026, 7, 10), date(2026, 7, 1))


# ---- isolated team fixture ----

@pytest.fixture(scope="module")
def team():
    """Create manager + report + an unrelated manager, each with big balances."""
    db = SessionLocal()
    created_ids: dict[str, int] = {}
    try:
        dept = db.scalar(select(Department).limit(1))
        types = list(db.scalars(select(LeaveType)))
        suffix = "isolteam"

        def mk(role: RBACRole, first: str, manager_id=None) -> Employee:
            emp = Employee(
                first_name=first,
                last_name="Iso",
                work_email=f"{first.lower()}.{suffix}@peopledesk.io",
                title="Test",
                location="Remote",
                hire_date=date(2020, 1, 1),
                department_id=dept.id,
                manager_id=manager_id,
            )
            db.add(emp)
            db.flush()
            for lt in types:
                db.add(LeaveBalance(employee_id=emp.id, leave_type_id=lt.id, accrued=100, used=0))
            db.add(
                User(
                    email=emp.work_email,
                    password_hash=hash_password(PW),
                    rbac_role=role,
                    employee_id=emp.id,
                )
            )
            return emp

        manager = mk(RBACRole.manager, "Mgr")
        report = mk(RBACRole.employee, "Rep", manager_id=manager.id)
        other_mgr = mk(RBACRole.manager, "Othr")
        db.commit()
        info = {
            "manager_email": manager.work_email,
            "report_email": report.work_email,
            "other_mgr_email": other_mgr.work_email,
            "report_id": report.id,
            "type_by_code": {lt.code: lt.id for lt in types},
        }
        created_ids = {
            "emp": [manager.id, report.id, other_mgr.id],
        }
        yield info
    finally:
        # teardown: remove requests, balances, users, employees we created
        emp_ids = created_ids.get("emp", [])
        if emp_ids:
            db.execute(delete(LeaveRequest).where(LeaveRequest.employee_id.in_(emp_ids)))
            db.execute(delete(LeaveBalance).where(LeaveBalance.employee_id.in_(emp_ids)))
            db.execute(delete(User).where(User.employee_id.in_(emp_ids)))
            db.execute(delete(Employee).where(Employee.id.in_(emp_ids)))
            db.commit()
        db.close()


def _headers(client, email, password=PW):
    tok = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _next_weekday(offset: int) -> date:
    d = date.today() + timedelta(days=offset)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


# ---- API: balance + full request lifecycle ----

def test_balance_endpoint(client, auth_headers):
    r = client.get("/leave/balance", headers=auth_headers["employee"])
    assert r.status_code == 200
    for b in r.json():
        assert b["available"] == pytest.approx(b["accrued"] - b["used"])


def test_submit_then_approve_flow(client, team):
    rep_h = _headers(client, team["report_email"])
    mgr_h = _headers(client, team["manager_email"])
    annual_id = team["type_by_code"]["ANNUAL"]

    start = _next_weekday(10)
    used_before = next(
        b["used"] for b in client.get("/leave/balance", headers=rep_h).json()
        if b["leave_type_id"] == annual_id
    )

    create = client.post(
        "/leave/requests",
        headers=rep_h,
        json={"leave_type_id": annual_id, "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "vacation"},
    )
    assert create.status_code == 201, create.text
    req = create.json()
    assert req["status"] == "pending" and req["days"] == 1

    used_after = next(
        b["used"] for b in client.get("/leave/balance", headers=rep_h).json()
        if b["leave_type_id"] == annual_id
    )
    assert used_after == pytest.approx(used_before + 1)

    assert any(q["id"] == req["id"] for q in client.get("/leave/approvals", headers=mgr_h).json())

    ok = client.post(f"/leave/requests/{req['id']}/approve", headers=mgr_h, json={"note": "ok"})
    assert ok.status_code == 200 and ok.json()["status"] == "approved"

    used_final = next(
        b["used"] for b in client.get("/leave/balance", headers=rep_h).json()
        if b["leave_type_id"] == annual_id
    )
    assert used_final == pytest.approx(used_before + 1)  # approved days stay held


def test_reject_releases_hold(client, team):
    rep_h = _headers(client, team["report_email"])
    mgr_h = _headers(client, team["manager_email"])
    sick_id = team["type_by_code"]["SICK"]
    start = _next_weekday(20)

    used_before = next(
        b["used"] for b in client.get("/leave/balance", headers=rep_h).json()
        if b["leave_type_id"] == sick_id
    )
    req = client.post(
        "/leave/requests",
        headers=rep_h,
        json={"leave_type_id": sick_id, "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "x"},
    ).json()
    client.post(f"/leave/requests/{req['id']}/reject", headers=mgr_h, json={"note": "no"})
    used_after = next(
        b["used"] for b in client.get("/leave/balance", headers=rep_h).json()
        if b["leave_type_id"] == sick_id
    )
    assert used_after == pytest.approx(used_before)


def test_cannot_approve_already_decided(client, team):
    rep_h = _headers(client, team["report_email"])
    mgr_h = _headers(client, team["manager_email"])
    casual_id = team["type_by_code"]["CASUAL"]
    start = _next_weekday(30)
    req = client.post(
        "/leave/requests",
        headers=rep_h,
        json={"leave_type_id": casual_id, "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "x"},
    ).json()
    client.post(f"/leave/requests/{req['id']}/approve", headers=mgr_h, json={})
    again = client.post(f"/leave/requests/{req['id']}/reject", headers=mgr_h, json={})
    assert again.status_code == 400  # illegal transition


def test_employee_cannot_access_approvals(client, auth_headers):
    assert client.get("/leave/approvals", headers=auth_headers["employee"]).status_code == 403


def test_manager_cannot_approve_non_report(client, team):
    """A plain manager must not decide a request from someone who isn't their report."""
    rep_h = _headers(client, team["report_email"])
    other_h = _headers(client, team["other_mgr_email"])  # manager of nobody relevant
    annual_id = team["type_by_code"]["ANNUAL"]
    start = _next_weekday(40)
    req = client.post(
        "/leave/requests",
        headers=rep_h,
        json={"leave_type_id": annual_id, "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "x"},
    ).json()
    resp = client.post(f"/leave/requests/{req['id']}/approve", headers=other_h, json={})
    assert resp.status_code == 403
    client.post(f"/leave/requests/{req['id']}/cancel", headers=rep_h)
