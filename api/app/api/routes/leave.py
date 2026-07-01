"""Leave / PTO: balances, requests, manager approval queue."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, has_min_role, require_min_role
from app.database import get_db
from app.models.employee import Employee
from app.models.enums import LeaveStatus, RBACRole
from app.models.leave import LeaveRequest, LeaveType
from app.models.user import User
from app.schemas.leave import (
    LeaveBalanceOut,
    LeaveDecision,
    LeaveRequestCreate,
    LeaveRequestOut,
    LeaveTypeOut,
)
from app.services import leave as leave_svc

router = APIRouter(prefix="/leave", tags=["leave"])


def _require_employee(user: User) -> Employee:
    if user.employee is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account is not linked to an employee profile",
        )
    return user.employee


def _out(req: LeaveRequest, *, with_employee: bool = False) -> LeaveRequestOut:
    data = LeaveRequestOut.model_validate(req)
    if req.leave_type is not None:
        data.leave_type_name = req.leave_type.name
    if not with_employee:
        data.employee = None
    return data


@router.get("/types", response_model=list[LeaveTypeOut])
def list_types(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[LeaveType]:
    return list(db.scalars(select(LeaveType).order_by(LeaveType.name)))


@router.get("/balance", response_model=list[LeaveBalanceOut])
def my_balance(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[LeaveBalanceOut]:
    emp = _require_employee(user)
    return [LeaveBalanceOut(**b) for b in leave_svc.compute_balances(db, emp.id)]


@router.get("/requests", response_model=list[LeaveRequestOut])
def my_requests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status_filter: Optional[LeaveStatus] = Query(default=None, alias="status"),
) -> list[LeaveRequestOut]:
    emp = _require_employee(user)
    stmt = (
        select(LeaveRequest)
        .options(selectinload(LeaveRequest.leave_type))
        .where(LeaveRequest.employee_id == emp.id)
        .order_by(LeaveRequest.created_at.desc())
    )
    if status_filter is not None:
        stmt = stmt.where(LeaveRequest.status == status_filter)
    return [_out(r) for r in db.scalars(stmt)]


@router.post("/requests", response_model=LeaveRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LeaveRequestOut:
    emp = _require_employee(user)
    try:
        req = leave_svc.submit_request(
            db,
            employee=emp,
            actor_user_id=user.id,
            leave_type_id=payload.leave_type_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            reason=payload.reason,
        )
    except leave_svc.LeaveValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    db.refresh(req)
    return _out(req)


@router.post("/requests/{request_id}/cancel", response_model=LeaveRequestOut)
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LeaveRequestOut:
    req = db.get(LeaveRequest, request_id, options=[selectinload(LeaveRequest.leave_type)])
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    try:
        leave_svc.cancel_request(db, request=req, actor=user)
    except leave_svc.LeavePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except leave_svc.LeaveValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _out(req)


# ---- Manager / HR approval surface ----

@router.get("/approvals", response_model=list[LeaveRequestOut])
def approval_queue(
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.manager)),
) -> list[LeaveRequestOut]:
    """Pending requests this manager can act on (their direct reports).

    hr_admin+ see all pending requests.
    """
    stmt = (
        select(LeaveRequest)
        .options(
            selectinload(LeaveRequest.leave_type),
            selectinload(LeaveRequest.employee),
        )
        .where(LeaveRequest.status == LeaveStatus.pending)
        .order_by(LeaveRequest.created_at.asc())
    )
    if not has_min_role(user, RBACRole.hr_admin):
        # only direct reports of this manager
        report_ids = [
            e.id
            for e in db.scalars(
                select(Employee).where(Employee.manager_id == user.employee_id)
            )
        ]
        if not report_ids:
            return []
        stmt = stmt.where(LeaveRequest.employee_id.in_(report_ids))
    return [_out(r, with_employee=True) for r in db.scalars(stmt)]


@router.post("/requests/{request_id}/approve", response_model=LeaveRequestOut)
def approve_request(
    request_id: int,
    payload: LeaveDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.manager)),
) -> LeaveRequestOut:
    return _decide(db, request_id, user, approve=True, note=payload.note)


@router.post("/requests/{request_id}/reject", response_model=LeaveRequestOut)
def reject_request(
    request_id: int,
    payload: LeaveDecision,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.manager)),
) -> LeaveRequestOut:
    return _decide(db, request_id, user, approve=False, note=payload.note)


def _decide(db: Session, request_id: int, user: User, *, approve: bool, note: str) -> LeaveRequestOut:
    req = db.get(
        LeaveRequest,
        request_id,
        options=[selectinload(LeaveRequest.leave_type), selectinload(LeaveRequest.employee)],
    )
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    try:
        leave_svc.decide_request(db, request=req, actor=user, approve=approve, note=note)
    except leave_svc.LeavePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except leave_svc.LeaveValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _out(req, with_employee=True)
