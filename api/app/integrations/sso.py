"""SSO provider interface + mock.

MOCK: no real IdP. `verify_assertion` just echoes a deterministic identity.
Swap MockSSOProvider for an Okta/Azure AD implementation later.
"""

from __future__ import annotations

from typing import Protocol


class SSOProvider(Protocol):
    def verify_assertion(self, token: str) -> dict:  # pragma: no cover - interface
        ...


class MockSSOProvider:
    """MOCK SSO — accepts any token, returns a stub identity."""

    def verify_assertion(self, token: str) -> dict:
        return {
            "mock": True,
            "subject": token[:32] if token else "unknown",
            "note": "MOCK SSO — no real identity provider is contacted.",
        }
