from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(Base, TimestampMixin):
    __tablename__ = "department"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department"
    )
