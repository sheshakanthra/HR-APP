"""Policy RAG: ingestion (chunk → embed → pgvector) and grounded retrieval.

Retrieval only ever returns chunks from PUBLISHED documents, and each result
carries its source doc title + version so answers can be cited. A relevance
threshold prevents the agent from grounding on weak matches (which would let it
"answer" questions the policy base doesn't cover).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PolicyStatus
from app.models.policy import PolicyChunk, PolicyDocument
from app.services.chunking import chunk_text
from app.services.embeddings import embed_documents, embed_query

# Cosine-similarity floor for a chunk to count as relevant. bge-small produces
# normalized vectors; empirically ~0.55+ similarity is a solid topical match,
# so we keep the floor conservative to avoid ungrounded answers.
DEFAULT_MIN_SIMILARITY = 0.55
DEFAULT_TOP_K = 4


def ingest_document(db: Session, document: PolicyDocument, *, commit: bool = True) -> int:
    """(Re)build the vector index for one document.

    Deletes existing chunks, and — only if the doc is published — re-chunks,
    embeds, and stores fresh vectors. Returns the number of chunks written.
    """
    db.query(PolicyChunk).filter(
        PolicyChunk.policy_document_id == document.id
    ).delete(synchronize_session=False)

    if document.status != PolicyStatus.published:
        if commit:
            db.commit()
        return 0

    chunks = chunk_text(document.body)
    embeddings = embed_documents(chunks)
    for idx, (text, vector) in enumerate(zip(chunks, embeddings)):
        db.add(
            PolicyChunk(
                policy_document_id=document.id,
                chunk_index=idx,
                chunk_text=text,
                doc_version=document.version,
                doc_title=document.title,
                embedding=vector,
            )
        )
    if commit:
        db.commit()
    return len(chunks)


def search_policy_docs(
    db: Session,
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
) -> list[dict]:
    """Semantic search over published policy chunks.

    Returns a list of dicts (highest similarity first), each with the chunk text
    and its source citation. Empty list => nothing relevant found (the agent
    must then say so and offer to escalate — never guess).
    """
    query = (query or "").strip()
    if not query:
        return []

    query_vec = embed_query(query)
    distance = PolicyChunk.embedding.cosine_distance(query_vec).label("distance")

    rows = db.execute(
        select(PolicyChunk, distance)
        .join(PolicyDocument, PolicyDocument.id == PolicyChunk.policy_document_id)
        .where(PolicyDocument.status == PolicyStatus.published)
        .order_by(distance.asc())
        .limit(top_k)
    ).all()

    results: list[dict] = []
    for chunk, dist in rows:
        similarity = 1.0 - float(dist)
        if similarity >= min_similarity:
            results.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": chunk.policy_document_id,
                    "doc_title": chunk.doc_title,
                    "doc_version": chunk.doc_version,
                    "chunk_text": chunk.chunk_text,
                    "similarity": round(similarity, 4),
                }
            )
    return results
