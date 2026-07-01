"""Deterministic text chunking for policy documents.

Splits on paragraph breaks, then packs sentences into ~target-sized chunks with
a small sentence overlap so context isn't lost at boundaries.
"""

from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text.strip()) if s.strip()]


def chunk_text(text: str, *, target_chars: int = 600, overlap_sentences: int = 1) -> list[str]:
    """Return a list of chunk strings (never empty for non-empty input)."""
    text = (text or "").strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()] or [text]
    chunks: list[str] = []

    for para in paragraphs:
        sentences = _sentences(para) or [para]
        current: list[str] = []
        current_len = 0
        for sentence in sentences:
            if current and current_len + len(sentence) > target_chars:
                chunks.append(" ".join(current))
                current = current[-overlap_sentences:] if overlap_sentences else []
                current_len = sum(len(s) + 1 for s in current)
            current.append(sentence)
            current_len += len(sentence) + 1
        if current:
            chunks.append(" ".join(current))

    return chunks
