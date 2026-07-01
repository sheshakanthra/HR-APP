"""Calendar interface + mock.

MOCK: pretends to create an out-of-office event; returns a fake event id.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Protocol


class CalendarProvider(Protocol):
    def create_ooo_event(
        self, email: str, start: date, end: date, title: str
    ) -> dict:  # pragma: no cover - interface
        ...


class MockCalendarProvider:
    """MOCK calendar — returns a synthetic event id, contacts nothing."""

    def create_ooo_event(self, email: str, start: date, end: date, title: str) -> dict:
        return {
            "mock": True,
            "event_id": f"mock-{uuid.uuid4().hex[:12]}",
            "email": email,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "title": title,
        }
