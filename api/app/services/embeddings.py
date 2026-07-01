"""Local embedding model (fastembed) — NOT Groq.

Groq serves generation only; there is no Groq embeddings endpoint. We embed
locally with BAAI/bge-small-en-v1.5 (384-dim) and store vectors in pgvector.

The model is lazily loaded once per process (first call downloads weights,
~130MB, then cached under the container's HF cache).
"""

from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _model():
    # Imported lazily so importing this module (e.g. in Alembic) is cheap.
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.embedding_model)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed passages for storage. bge uses a passage-specific instruction."""
    if not texts:
        return []
    return [vec.tolist() for vec in _model().passage_embed(list(texts))]


def embed_query(text: str) -> list[float]:
    """Embed a search query (bge query instruction improves retrieval)."""
    return next(iter(_model().query_embed([text]))).tolist()


def warmup() -> None:
    """Force model load (used by the ingest script / optional startup)."""
    embed_query("warmup")
