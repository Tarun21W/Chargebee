"""Per-customer semantic retrieval over Supabase pgvector.

Embeds the query with BGE-M3 and runs a cosine-distance nearest-neighbour search
scoped to a single customer. Degrades to an empty list if embeddings are absent
(e.g. Ollama was unavailable during seeding) so callers can fall back to
structured facts only.
"""
from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.llm import embed_query

log = get_logger("app.rag")

_SQL = text(
    """
    SELECT chunk_text, source_type, source_id,
           1 - (embedding <=> (:qvec)::vector) AS score
    FROM doc_chunks
    WHERE customer_id = :cid AND embedding IS NOT NULL
    ORDER BY embedding <=> (:qvec)::vector
    LIMIT :k
    """
)


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def retrieve(db: Session, customer_id: uuid.UUID, query: str, k: int = 6) -> list[dict]:
    try:
        qvec = embed_query(query)
    except Exception as exc:  # noqa: BLE001
        log.warning("Query embedding failed: %s. Returning no RAG context.", exc)
        return []

    rows = db.execute(
        _SQL, {"qvec": _vec_literal(qvec), "cid": str(customer_id), "k": k}
    ).all()
    return [
        {
            "chunk_text": r.chunk_text,
            "source_type": r.source_type,
            "source_id": r.source_id,
            "score": float(r.score) if r.score is not None else None,
        }
        for r in rows
    ]
