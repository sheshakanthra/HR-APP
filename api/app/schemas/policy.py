from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PolicyStatus


class PolicyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    version: int
    status: PolicyStatus
    effective_date: Optional[date] = None
    updated_at: datetime


class PolicyOut(PolicyBrief):
    body: str
    chunk_count: Optional[int] = None


class PolicyCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    category: str = Field(default="General", max_length=120)
    body: str = Field(min_length=1)
    effective_date: Optional[date] = None


class PolicyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    category: Optional[str] = Field(default=None, max_length=120)
    body: Optional[str] = Field(default=None, min_length=1)
    effective_date: Optional[date] = None


class PolicySearchResult(BaseModel):
    chunk_id: int
    document_id: int
    doc_title: str
    doc_version: int
    chunk_text: str
    similarity: float


class PolicySearchResponse(BaseModel):
    query: str
    results: list[PolicySearchResult]
    grounded: bool
