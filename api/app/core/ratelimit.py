"""Lightweight in-memory per-IP rate limiting as a FastAPI dependency.

Kept dependency-based (not a decorator) so it never interferes with request-body
parsing. Sliding-window per (client IP, bucket). Single-process; for multi-worker
deployments back this with Redis. Disabled when APP_ENV=test.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import settings

_WINDOW = 60.0  # seconds
_hits: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(bucket: str, limit: int):
    def dependency(request: Request) -> None:
        if settings.app_env == "test":
            return
        ip = request.client.host if request.client else "unknown"
        key = f"{bucket}:{ip}"
        now = time.monotonic()
        q = _hits[key]
        while q and now - q[0] > _WINDOW:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again shortly.",
            )
        q.append(now)

    return dependency
