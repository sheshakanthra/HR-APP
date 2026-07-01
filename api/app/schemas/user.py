from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import RBACRole


class EmployeeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    work_email: EmailStr
    title: str
    department_id: Optional[int] = None
    manager_id: Optional[int] = None


class UserOut(BaseModel):
    """Safe user representation — never includes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    rbac_role: RBACRole
    is_active: bool
    employee_id: Optional[int] = None


class MeOut(BaseModel):
    user: UserOut
    employee: Optional[EmployeeBrief] = None
