from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import LeaveStatus

if TYPE_CHECKING:
    from app.models.employee import Employee


class LeaveType(Base, TimestampMixin):
    __tablename__ = "leave_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    # Annual accrual entitlement in days; used deterministically by leave service.
    annual_accrual_days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class LeaveBalance(Base, TimestampMixin):
    __tablename__ = "leave_balance"
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id", name="uq_balance_employee_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey("leave_type.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Deterministic math: available = accrued - used. `used` counts approved + pending.
    accrued: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    used: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)

    employee: Mapped["Employee"] = relationship(
        back_populates="balances", foreign_keys=[employee_id]
    )
    leave_type: Mapped["LeaveType"] = relationship()

    @property
    def available(self) -> float:
        return float(self.accrued) - float(self.used)


class LeaveRequest(Base, TimestampMixin):
    __tablename__ = "leave_request"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey("leave_type.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    status: Mapped[LeaveStatus] = mapped_column(
        SAEnum(LeaveStatus, name="leave_status"), nullable=False, default=LeaveStatus.pending
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), nullable=True, index=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    # Provenance: was this request created by the AI agent on the user's behalf?
    created_via_agent: Mapped[bool] = mapped_column(default=False, nullable=False)

    employee: Mapped["Employee"] = relationship(
        back_populates="leave_requests", foreign_keys=[employee_id]
    )
    approver: Mapped[Optional["Employee"]] = relationship(foreign_keys=[approver_id])
    leave_type: Mapped["LeaveType"] = relationship()
