from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import LeaveStatus


class LeaveTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    annual_accrual_days: float
    description: str


class LeaveBalanceOut(BaseModel):
    leave_type_id: int
    leave_type_name: str
    leave_type_code: str
    accrued: float
    used: float
    available: float


class LeaveRequestCreate(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str = Field(default="", max_length=1000)

    @field_validator("end_date")
    @classmethod
    def _end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start is not None and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v


class LeaveDecision(BaseModel):
    note: str = Field(default="", max_length=1000)


class EmployeeRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    work_email: str


class LeaveRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    leave_type_id: int
    leave_type_name: Optional[str] = None
    start_date: date
    end_date: date
    days: float
    reason: str
    status: LeaveStatus
    approver_id: Optional[int] = None
    decided_at: Optional[datetime] = None
    decision_note: str
    created_via_agent: bool
    created_at: datetime
    employee: Optional[EmployeeRef] = None
