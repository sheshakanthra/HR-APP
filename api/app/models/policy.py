from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.models.base import Base, TimestampMixin
from app.models.enums import PolicyStatus

if TYPE_CHECKING:
    pass


class PolicyDocument(Base, TimestampMixin):
    __tablename__ = "policy_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), nullable=False, default="General")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[PolicyStatus] = mapped_column(
        SAEnum(PolicyStatus, name="policy_status"), nullable=False, default=PolicyStatus.draft
    )
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    chunks: Mapped[list["PolicyChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class PolicyChunk(Base, TimestampMixin):
    __tablename__ = "policy_chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_document_id: Mapped[int] = mapped_column(
        ForeignKey("policy_document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Snapshot of doc version at embed time so citations stay accurate across re-publish.
    doc_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    doc_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim), nullable=False)

    document: Mapped["PolicyDocument"] = relationship(back_populates="chunks")
