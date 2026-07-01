"""Policy Knowledge Base: CRUD (hr_admin+), publish/ingest, and RAG search."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, has_min_role, require_min_role
from app.core.audit import record
from app.database import get_db
from app.models.enums import PolicyStatus, RBACRole
from app.models.policy import PolicyChunk, PolicyDocument
from app.models.user import User
from app.schemas.policy import (
    PolicyBrief,
    PolicyCreate,
    PolicyOut,
    PolicySearchResponse,
    PolicySearchResult,
    PolicyUpdate,
)
from app.services import policy_rag

router = APIRouter(prefix="/policies", tags=["policy"])


def _chunk_count(db: Session, doc_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(PolicyChunk).where(
            PolicyChunk.policy_document_id == doc_id
        )
    ) or 0


def _out(db: Session, doc: PolicyDocument) -> PolicyOut:
    data = PolicyOut.model_validate(doc)
    data.chunk_count = _chunk_count(db, doc.id)
    return data


@router.get("", response_model=list[PolicyBrief])
def list_policies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    category: Optional[str] = Query(default=None),
) -> list[PolicyDocument]:
    stmt = select(PolicyDocument).order_by(PolicyDocument.title)
    # Employees/managers only see published policies; hr_admin+ see drafts too.
    if not has_min_role(user, RBACRole.hr_admin):
        stmt = stmt.where(PolicyDocument.status == PolicyStatus.published)
    if category:
        stmt = stmt.where(PolicyDocument.category == category)
    return list(db.scalars(stmt))


@router.get("/search", response_model=PolicySearchResponse)
def search_policies(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    q: str = Query(min_length=2),
    top_k: int = Query(default=policy_rag.DEFAULT_TOP_K, ge=1, le=10),
) -> PolicySearchResponse:
    """Grounded semantic search over published policy — the same retrieval the
    agent's `search_policy_docs` tool uses."""
    results = policy_rag.search_policy_docs(db, q, top_k=top_k)
    return PolicySearchResponse(
        query=q,
        results=[PolicySearchResult(**r) for r in results],
        grounded=len(results) > 0,
    )


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PolicyOut:
    doc = db.get(PolicyDocument, policy_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    if doc.status != PolicyStatus.published and not has_min_role(user, RBACRole.hr_admin):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return _out(db, doc)


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.hr_admin)),
) -> PolicyOut:
    doc = PolicyDocument(
        title=payload.title,
        category=payload.category,
        body=payload.body,
        version=1,
        status=PolicyStatus.draft,
        effective_date=payload.effective_date,
    )
    db.add(doc)
    db.flush()
    record(db, actor_user_id=user.id, action="policy.create", entity_type="policy_document",
           entity_id=doc.id, commit=False)
    db.commit()
    db.refresh(doc)
    return _out(db, doc)


@router.put("/{policy_id}", response_model=PolicyOut)
def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.hr_admin)),
) -> PolicyOut:
    doc = db.get(PolicyDocument, policy_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    body_changed = payload.body is not None and payload.body != doc.body
    for field in ("title", "category", "body", "effective_date"):
        val = getattr(payload, field)
        if val is not None:
            setattr(doc, field, val)

    # Editing a published doc creates a new version and re-indexes it.
    reindex = False
    if doc.status == PolicyStatus.published and body_changed:
        doc.version += 1
        reindex = True
    db.flush()
    if reindex:
        policy_rag.ingest_document(db, doc, commit=False)
    record(db, actor_user_id=user.id, action="policy.update", entity_type="policy_document",
           entity_id=doc.id, metadata={"reindexed": reindex}, commit=False)
    db.commit()
    db.refresh(doc)
    return _out(db, doc)


@router.post("/{policy_id}/publish", response_model=PolicyOut)
def publish_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.hr_admin)),
) -> PolicyOut:
    doc = db.get(PolicyDocument, policy_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    if doc.status == PolicyStatus.published:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already published")

    doc.status = PolicyStatus.published
    db.flush()
    n = policy_rag.ingest_document(db, doc, commit=False)
    record(db, actor_user_id=user.id, action="policy.publish", entity_type="policy_document",
           entity_id=doc.id, metadata={"chunks": n, "version": doc.version}, commit=False)
    db.commit()
    db.refresh(doc)
    return _out(db, doc)


@router.post("/{policy_id}/unpublish", response_model=PolicyOut)
def unpublish_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.hr_admin)),
) -> PolicyOut:
    doc = db.get(PolicyDocument, policy_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    doc.status = PolicyStatus.draft
    db.flush()
    # ingest_document with a draft doc removes its chunks.
    policy_rag.ingest_document(db, doc, commit=False)
    record(db, actor_user_id=user.id, action="policy.unpublish", entity_type="policy_document",
           entity_id=doc.id, commit=False)
    db.commit()
    db.refresh(doc)
    return _out(db, doc)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_min_role(RBACRole.hr_admin)),
) -> Response:
    doc = db.get(PolicyDocument, policy_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    record(db, actor_user_id=user.id, action="policy.delete", entity_type="policy_document",
           entity_id=doc.id, metadata={"title": doc.title}, commit=False)
    db.delete(doc)  # cascades to chunks
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
