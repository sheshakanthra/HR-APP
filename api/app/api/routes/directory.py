"""Employee directory, profiles, and org chart."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, has_min_role
from app.database import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.enums import RBACRole
from app.models.user import User
from app.schemas.directory import (
    DepartmentOut,
    EmployeeCard,
    EmployeeProfile,
    EmployeeSearchPage,
    ManagerRef,
    OrgNode,
)

router = APIRouter(prefix="/directory", tags=["directory"])


def _card(emp: Employee) -> EmployeeCard:
    return EmployeeCard(
        id=emp.id,
        first_name=emp.first_name,
        last_name=emp.last_name,
        work_email=emp.work_email,
        title=emp.title,
        department_id=emp.department_id,
        department_name=emp.department.name if emp.department else None,
        manager_id=emp.manager_id,
    )


def _can_view_extended(actor: User, target: Employee) -> bool:
    if has_min_role(actor, RBACRole.hr_admin):
        return True
    if actor.employee_id is None:
        return False
    if actor.employee_id == target.id:  # self
        return True
    if target.manager_id == actor.employee_id:  # direct report
        return True
    return False


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.name)))


@router.get("/employees", response_model=EmployeeSearchPage)
def search_employees(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    search: Optional[str] = Query(default=None),
    department_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> EmployeeSearchPage:
    stmt = select(Employee).options(selectinload(Employee.department))
    count_stmt = select(func.count()).select_from(Employee)

    if search:
        like = f"%{search.strip()}%"
        cond = or_(
            Employee.first_name.ilike(like),
            Employee.last_name.ilike(like),
            Employee.work_email.ilike(like),
            Employee.title.ilike(like),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if department_id is not None:
        stmt = stmt.where(Employee.department_id == department_id)
        count_stmt = count_stmt.where(Employee.department_id == department_id)

    total = db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Employee.first_name, Employee.last_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [_card(e) for e in db.scalars(stmt)]
    return EmployeeSearchPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/employees/{employee_id}", response_model=EmployeeProfile)
def get_profile(
    employee_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> EmployeeProfile:
    emp = db.get(
        Employee,
        employee_id,
        options=[
            selectinload(Employee.department),
            selectinload(Employee.manager),
            selectinload(Employee.reports).selectinload(Employee.department),
        ],
    )
    if emp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    card = _card(emp)
    manager_ref = ManagerRef.model_validate(emp.manager) if emp.manager else None

    if not _can_view_extended(actor, emp):
        # Contact-level only; still return the shape but without sensitive fields
        # collapsed to safe defaults would break typing, so 403 the extended view.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may view this person's directory card but not their full record",
        )

    return EmployeeProfile(
        **card.model_dump(),
        location=emp.location,
        hire_date=emp.hire_date,
        employment_status=emp.employment_status,
        manager=manager_ref,
        direct_reports=[_card(r) for r in emp.reports],
    )


@router.get("/employees/{employee_id}/card", response_model=EmployeeCard)
def get_card(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> EmployeeCard:
    """Contact-level card — available to any authenticated user."""
    emp = db.get(Employee, employee_id, options=[selectinload(Employee.department)])
    if emp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return _card(emp)


@router.get("/org-chart", response_model=list[OrgNode])
def org_chart(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[OrgNode]:
    """Full reporting tree rooted at employees with no manager."""
    employees = list(db.scalars(select(Employee).options(selectinload(Employee.department))))
    children: dict[int, list[Employee]] = {}
    roots: list[Employee] = []
    for e in employees:
        if e.manager_id is None:
            roots.append(e)
        else:
            children.setdefault(e.manager_id, []).append(e)

    def build(emp: Employee) -> OrgNode:
        kids = sorted(children.get(emp.id, []), key=lambda x: (x.first_name, x.last_name))
        return OrgNode(
            id=emp.id,
            first_name=emp.first_name,
            last_name=emp.last_name,
            title=emp.title,
            department_name=emp.department.name if emp.department else None,
            reports=[build(k) for k in kids],
        )

    return [build(r) for r in sorted(roots, key=lambda x: (x.first_name, x.last_name))]
