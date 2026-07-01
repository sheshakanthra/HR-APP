"""AI agent endpoints. Self-scoped: a user only ever sees their own conversations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.ratelimit import rate_limit
from app.database import get_db
from app.models.agent import AgentConversation, AgentMessage
from app.models.user import User
from app.schemas.agent import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationOut,
    MessageOut,
)
from app.services.agent.groq_client import get_groq_client
from app.services.agent.service import run_chat

router = APIRouter(prefix="/agent", tags=["agent"])


def _owned(db: Session, conversation_id: int, user: User) -> AgentConversation:
    conv = db.get(AgentConversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[AgentConversation]:
    return list(
        db.scalars(
            select(AgentConversation)
            .where(AgentConversation.user_id == user.id)
            .order_by(AgentConversation.id.desc())
        )
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConversationDetail:
    conv = _owned(db, conversation_id, user)
    # Only surface user/assistant turns in the UI transcript; tool rows are audit.
    turns = [
        MessageOut.model_validate(m) for m in conv.messages if m.role in ("user", "assistant")
    ]
    return ConversationDetail(
        id=conv.id, title=conv.title, created_at=conv.created_at, messages=turns
    )


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit("agent_chat", 20))])
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    if payload.conversation_id is not None:
        conv = _owned(db, payload.conversation_id, user)
    else:
        conv = AgentConversation(user_id=user.id, title=payload.message[:60])
        db.add(conv)
        db.flush()

    reply = run_chat(
        db,
        user=user,
        conversation=conv,
        user_text=payload.message,
        client=get_groq_client(),
    )
    return ChatResponse(conversation_id=conv.id, reply=MessageOut.model_validate(reply))
