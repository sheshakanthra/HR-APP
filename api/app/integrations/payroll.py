"""Payroll interface + mock.

MOCK: returns deterministic stub data. Never exposes real compensation and is
NOT surfaced through the employee agent (comp is out of the agent's scope).
"""

from __future__ import annotations

from typing import Protocol


class PayrollProvider(Protocol):
    def sync_leave_deduction(self, employee_id: int, days: float) -> dict:  # pragma: no cover
        ...


class MockPayrollProvider:
    """MOCK payroll — acknowledges a sync without touching any real system."""

    def sync_leave_deduction(self, employee_id: int, days: float) -> dict:
        return {
            "mock": True,
            "employee_id": employee_id,
            "days": days,
            "note": "MOCK payroll — no real payroll system is contacted.",
        }
