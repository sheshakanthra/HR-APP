from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import EmploymentStatus

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.leave import LeaveBalance, LeaveRequest
    from app.models.user import User


class Employee(Base, TimestampMixin):
    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    work_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(120), nullable=False, default="Remote")
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    employment_status: Mapped[EmploymentStatus] = mapped_column(
        SAEnum(EmploymentStatus, name="employment_status"),
        nullable=False,
        default=EmploymentStatus.active,
    )

    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("department.id", ondelete="SET NULL"), nullable=True, index=True
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), nullable=True, index=True
    )

    department: Mapped[Optional["Department"]] = relationship(back_populates="employees")
    manager: Mapped[Optional["Employee"]] = relationship(
        remote_side="Employee.id", back_populates="reports"
    )
    reports: Mapped[list["Employee"]] = relationship(back_populates="manager")

    user: Mapped[Optional["User"]] = relationship(back_populates="employee")

    balances: Mapped[list["LeaveBalance"]] = relationship(
        back_populates="employee",
        foreign_keys="LeaveBalance.employee_id",
        cascade="all, delete-orphan",
    )
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        back_populates="employee",
        foreign_keys="LeaveRequest.employee_id",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
