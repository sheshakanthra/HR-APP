from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import RBACRole

if TYPE_CHECKING:
    from app.models.employee import Employee


class User(Base, TimestampMixin):
    """Auth identity. 1:1 with Employee."""

    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rbac_role: Mapped[RBACRole] = mapped_column(
        SAEnum(RBACRole, name="rbac_role"), nullable=False, default=RBACRole.employee
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    employee: Mapped[Optional["Employee"]] = relationship(back_populates="user")
