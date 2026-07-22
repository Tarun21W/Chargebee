"""Ingestion endpoints — embedding backfill and graph sync triggers."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.models.customer_data import DocChunk
from app.services.llm import embed_texts

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/embeddings")
def backfill_embeddings(
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("admin.manage")),
) -> dict:
    """Embed any doc_chunks missing an embedding (batched)."""
    pending = list(db.scalars(select(DocChunk).where(DocChunk.embedding.is_(None))).all())
    if not pending:
        return {"embedded": 0, "message": "All chunks already embedded."}

    batch = 64
    done = 0
    for i in range(0, len(pending), batch):
        window = pending[i : i + batch]
        vectors = embed_texts([c.chunk_text for c in window])
        for chunk, vec in zip(window, vectors):
            chunk.embedding = vec
        db.commit()
        done += len(window)
    return {"embedded": done}


@router.post("/graph/sync")
def graph_sync(
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("admin.manage")),
) -> dict:
    from app.services.graph.sync import sync_all

    counts = sync_all(db)
    return {"status": "ok", **counts}
