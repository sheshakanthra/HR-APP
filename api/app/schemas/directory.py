from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import EmploymentStatus


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ManagerRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    title: str
    work_email: EmailStr


class EmployeeCard(BaseModel):
    """Contact-level info — safe for any authenticated user (directory scope)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    work_email: EmailStr
    title: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    manager_id: Optional[int] = None


class EmployeeProfile(EmployeeCard):
    """Extended record — self, the employee's manager, or hr_admin+ only."""

    location: str
    hire_date: date
    employment_status: EmploymentStatus
    manager: Optional[ManagerRef] = None
    direct_reports: list[EmployeeCard] = []


class EmployeeSearchPage(BaseModel):
    items: list[EmployeeCard]
    total: int
    page: int
    page_size: int


class OrgNode(BaseModel):
    id: int
    first_name: str
    last_name: str
    title: str
    department_name: Optional[str] = None
    reports: list["OrgNode"] = []


OrgNode.model_rebuild()
