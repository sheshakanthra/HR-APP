"""Transparent, hand-rolled tool-dispatch loop over Groq (no agent framework).

The LLM client is injected so tests can drive the loop deterministically without
calling Groq. Every user/assistant/tool message and every tool call is persisted.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models.agent import AgentConversation, AgentMessage
from app.models.user import User
from app.services.agent.prompt import SYSTEM_PROMPT
from app.services.agent.tools import ToolContext, dispatch, groq_tool_schemas

MAX_TOOL_ROUNDS = 5


class LLMClient(Protocol):
    def create(self, messages: list[dict], tools: list[dict]) -> Any:  # pragma: no cover
        """Return an object with .content (str|None) and .tool_calls (list|None).

        Each tool_call has: .id, .function.name, .function.arguments (JSON str).
        """
        ...


def run_chat(
    db: Session,
    *,
    user: User,
    conversation: AgentConversation,
    user_text: str,
    client: LLMClient,
) -> AgentMessage:
    ctx = ToolContext(db=db, user=user)

    # Persist the user's message.
    db.add(AgentMessage(conversation_id=conversation.id, role="user", content=user_text))
    db.flush()

    # Rebuild the running transcript for the model.
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in conversation.messages:
        if m.role == "user":
            messages.append({"role": "user", "content": m.content})
        elif m.role == "assistant":
            messages.append({"role": "assistant", "content": m.content or ""})
        # persisted tool rows are omitted from replay to keep history simple

    tools = groq_tool_schemas()
    collected_sources: list[dict] = []

    for _round in range(MAX_TOOL_ROUNDS):
        response = client.create(messages=messages, tools=tools)
        tool_calls = getattr(response, "tool_calls", None) or []
        content = getattr(response, "content", None) or ""

        if not tool_calls:
            final = AgentMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=content,
                sources=collected_sources or None,
            )
            db.add(final)
            db.commit()
            db.refresh(final)
            return final

        # Assistant turn requesting tools.
        assistant_tc = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in tool_calls
        ]
        messages.append({"role": "assistant", "content": content, "tool_calls": assistant_tc})

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result, audit_meta = dispatch(ctx, name, args)

            if name == "search_policy_docs" and result.get("grounded"):
                for r in result["results"]:
                    collected_sources.append(
                        {"doc_title": r["doc_title"], "doc_version": r["doc_version"]}
                    )

            # Persist the tool call (name, args-minus-PII, status).
            db.add(
                AgentMessage(
                    conversation_id=conversation.id,
                    role="tool",
                    content=json.dumps(result)[:4000],
                    tool_calls=audit_meta,
                )
            )
            db.flush()

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": json.dumps(result),
                }
            )

    # Safety valve: too many tool rounds.
    final = AgentMessage(
        conversation_id=conversation.id,
        role="assistant",
        content="I wasn't able to complete that. Let me flag it for a human HR representative.",
        sources=collected_sources or None,
    )
    db.add(final)
    db.commit()
    db.refresh(final)
    return final
