"""Admin routes gated to hr_admin+ (audit log is read-only / append-only).

Expanded in Milestone 6; the audit-log reader lands here now so RBAC gating
has a real protected surface to test against.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_min_role
from app.database import get_db
from app.models.audit import AuditLog
from app.models.enums import RBACRole
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


class AuditEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[int]
    audit_metadata: Optional[Any]
    created_at: datetime


@router.get("/audit-log", response_model=list[AuditEntryOut])
def read_audit_log(
    db: Session = Depends(get_db),
    _: User = Depends(require_min_role(RBACRole.hr_admin)),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog).order_by(AuditLog.id.desc()).limit(limit).offset(offset)
        )
    )
