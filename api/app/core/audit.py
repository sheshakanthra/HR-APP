"""Append-only audit logging helper.

Every write and every agent tool call funnels through `record()`. Never logs
raw PII (redact before passing metadata) and never exposes a value like a
password or token.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record(
    db: Session,
    *,
    actor_user_id: Optional[int],
    action: str,
    entity_type: str = "",
    entity_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
    commit: bool = True,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        audit_metadata=metadata,
    )
    db.add(entry)
    if commit:
        db.commit()
    else:
        db.flush()
    return entry
