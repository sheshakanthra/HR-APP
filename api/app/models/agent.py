from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AgentConversation(Base, TimestampMixin):
    __tablename__ = "agent_conversation"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New conversation")

    messages: Mapped[list["AgentMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.id",
    )


class AgentMessage(Base, TimestampMixin):
    __tablename__ = "agent_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("agent_conversation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # role: user | assistant | tool | system
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Raw tool_calls emitted by the model (JSON) and/or tool results / cited sources.
    tool_calls: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    sources: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    conversation: Mapped["AgentConversation"] = relationship(back_populates="messages")


class HRTicket(Base, TimestampMixin):
    """Escalation ticket created by the agent's escalate_to_hr tool."""

    __tablename__ = "hr_ticket"

    id: Mapped[int] = mapped_column(primary_key=True)
    raised_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
