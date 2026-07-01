"""Leave service: deterministic balance math + approval state machine.

All leave-balance arithmetic and status transitions live here in plain Python
(never delegated to the LLM). `used` holds approved AND pending days, so
`available = accrued - used` reflects remaining days after outstanding holds.

State machine (enforced):
    pending  --approve-->  approved
    pending  --reject-->   rejected
    pending  --cancel-->   cancelled   (releases hold)
    approved --cancel-->   cancelled   (releases hold, future dates only)
No other transition is legal.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record
from app.models.employee import Employee
from app.models.enums import LeaveStatus, RBACRole
from app.models.leave import LeaveBalance, LeaveRequest, LeaveType
from app.models.user import User


class LeaveValidationError(ValueError):
    """Bad input / illegal transition -> HTTP 400."""


class LeavePermissionError(PermissionError):
    """Caller not allowed to act on this request -> HTTP 403."""


def business_days(start: date, end: date) -> int:
    """Inclusive count of weekdays (Mon-Fri) between two dates. Deterministic."""
    if end < start:
        raise LeaveValidationError("end_date must be on or after start_date")
    days = 0
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # 0=Mon .. 4=Fri
            days += 1
        cur = date.fromordinal(cur.toordinal() + 1)
    return days


def _get_balance(db: Session, employee_id: int, leave_type_id: int) -> LeaveBalance | None:
    return db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == leave_type_id,
        )
    )


def compute_balances(db: Session, employee_id: int) -> list[dict]:
    """Return the employee's balances with deterministic `available`."""
    rows = db.execute(
        select(LeaveBalance, LeaveType)
        .join(LeaveType, LeaveType.id == LeaveBalance.leave_type_id)
        .where(LeaveBalance.employee_id == employee_id)
        .order_by(LeaveType.name)
    ).all()
    out = []
    for bal, lt in rows:
        out.append(
            {
                "leave_type_id": lt.id,
                "leave_type_name": lt.name,
                "leave_type_code": lt.code,
                "accrued": float(bal.accrued),
                "used": float(bal.used),
                "available": float(bal.accrued) - float(bal.used),
            }
        )
    return out


def submit_request(
    db: Session,
    *,
    employee: Employee,
    actor_user_id: int,
    leave_type_id: int,
    start_date: date,
    end_date: date,
    reason: str,
    via_agent: bool = False,
) -> LeaveRequest:
    """Create a PENDING request routed to the employee's manager.

    Never auto-approves. Deducts the requested days as a hold on the balance.
    """
    leave_type = db.get(LeaveType, leave_type_id)
    if leave_type is None:
        raise LeaveValidationError("Unknown leave type")

    days = business_days(start_date, end_date)
    if days <= 0:
        raise LeaveValidationError("Leave must span at least one business day")

    balance = _get_balance(db, employee.id, leave_type_id)
    if balance is None:
        raise LeaveValidationError("No balance configured for this leave type")

    available = float(balance.accrued) - float(balance.used)
    if days > available:
        raise LeaveValidationError(
            f"Insufficient balance: requested {days} day(s), {available:g} available"
        )

    req = LeaveRequest(
        employee_id=employee.id,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        reason=reason or "",
        status=LeaveStatus.pending,
        approver_id=employee.manager_id,  # may be None (e.g. CEO) -> HR handles
        created_via_agent=via_agent,
    )
    # Hold the days on the balance immediately.
    balance.used = float(balance.used) + days
    db.add(req)
    db.flush()

    record(
        db,
        actor_user_id=actor_user_id,
        action="leave.submit",
        entity_type="leave_request",
        entity_id=req.id,
        metadata={
            "leave_type": leave_type.code,
            "days": days,
            "via_agent": via_agent,
            "approver_employee_id": employee.manager_id,
        },
        commit=False,
    )
    db.commit()
    return req


def _can_decide(db: Session, request: LeaveRequest, actor: User) -> bool:
    """A request may be decided by the owner's manager or by hr_admin+."""
    if actor.rbac_role in (RBACRole.hr_admin, RBACRole.super_admin):
        return True
    if actor.employee is None:
        return False
    owner = db.get(Employee, request.employee_id)
    return owner is not None and owner.manager_id == actor.employee.id


def decide_request(
    db: Session,
    *,
    request: LeaveRequest,
    actor: User,
    approve: bool,
    note: str = "",
) -> LeaveRequest:
    if request.status != LeaveStatus.pending:
        raise LeaveValidationError(
            f"Cannot decide a request in status '{request.status.value}'"
        )
    if not _can_decide(db, request, actor):
        raise LeavePermissionError("You cannot decide this leave request")

    if approve:
        request.status = LeaveStatus.approved
    else:
        request.status = LeaveStatus.rejected
        # release the hold
        balance = _get_balance(db, request.employee_id, request.leave_type_id)
        if balance is not None:
            balance.used = max(0.0, float(balance.used) - float(request.days))

    request.decided_at = datetime.now(timezone.utc)
    request.decision_note = note or ""
    if actor.employee is not None:
        request.approver_id = actor.employee.id

    record(
        db,
        actor_user_id=actor.id,
        action="leave.approve" if approve else "leave.reject",
        entity_type="leave_request",
        entity_id=request.id,
        metadata={"note_present": bool(note)},
        commit=False,
    )
    db.commit()
    return request


def cancel_request(db: Session, *, request: LeaveRequest, actor: User) -> LeaveRequest:
    """Owner cancels their own pending/approved request; releases the hold."""
    if actor.employee is None or request.employee_id != actor.employee.id:
        raise LeavePermissionError("You can only cancel your own leave requests")
    if request.status not in (LeaveStatus.pending, LeaveStatus.approved):
        raise LeaveValidationError(
            f"Cannot cancel a request in status '{request.status.value}'"
        )

    request.status = LeaveStatus.cancelled
    balance = _get_balance(db, request.employee_id, request.leave_type_id)
    if balance is not None:
        balance.used = max(0.0, float(balance.used) - float(request.days))

    record(
        db,
        actor_user_id=actor.id,
        action="leave.cancel",
        entity_type="leave_request",
        entity_id=request.id,
        commit=False,
    )
    db.commit()
    return request
