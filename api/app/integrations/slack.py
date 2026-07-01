"""Slack notification interface + mock.

MOCK: messages are appended to an in-memory list and logged, never sent.
"""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger("integrations.slack")


class SlackProvider(Protocol):
    def send(self, channel: str, text: str) -> dict:  # pragma: no cover - interface
        ...


class MockSlackProvider:
    """MOCK Slack — records notifications instead of sending them."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, channel: str, text: str) -> dict:
        payload = {"mock": True, "channel": channel, "text": text}
        self.sent.append(payload)
        logger.info("MOCK Slack -> %s: %s", channel, text)
        return payload
