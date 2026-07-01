"""Groq-backed LLM client (generation only). Normalizes the SDK response into
the small shape run_chat expects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list | None


class GroqClient:
    def __init__(self) -> None:
        from groq import Groq

        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    def create(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = resp.choices[0].message
        return LLMResponse(content=msg.content, tool_calls=msg.tool_calls or None)


def get_groq_client() -> GroqClient:
    return GroqClient()
