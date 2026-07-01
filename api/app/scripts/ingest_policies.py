"""(Re)build the pgvector index for all published policy documents.

Run after seeding (seed.py creates policy docs but not embeddings):
    python -m app.scripts.ingest_policies
"""

from __future__ import annotations

from sqlalchemy import select

from app.database import SessionLocal
from app.models.enums import PolicyStatus
from app.models.policy import PolicyDocument
from app.services.policy_rag import ingest_document


def main() -> None:
    db = SessionLocal()
    try:
        docs = list(
            db.scalars(
                select(PolicyDocument).where(PolicyDocument.status == PolicyStatus.published)
            )
        )
        print(f"[ingest] embedding {len(docs)} published policy document(s)…")
        total = 0
        for doc in docs:
            n = ingest_document(db, doc)
            total += n
            print(f"[ingest]   #{doc.id} '{doc.title}' v{doc.version} -> {n} chunk(s)")
        print(f"[ingest] done. {total} chunk(s) indexed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
