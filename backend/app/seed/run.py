"""Seed runner: `python -m app.seed.run`.

Populates the Supabase Postgres database with reference data + synthetic
customers, computes RAG embeddings, and (optionally) creates matching Supabase
Auth users and syncs the Neo4j graph. Embedding / auth / graph steps degrade
gracefully if their dependencies are unavailable.
"""
from __future__ import annotations

import sys

from sqlalchemy import text

from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.core.logging import configure_logging, get_logger
from app.models import customer_data  # noqa: F401  (ensure metadata is registered)
from app.seed.customers import seed_customers
from app.seed.reference import STAFF, seed_reference

configure_logging()
log = get_logger("app.seed")

SEED_PASSWORD = "Passw0rd!demo"  # shared demo password for seeded Supabase Auth users


def _truncate_all() -> None:
    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    log.info("Cleared %d tables.", len(Base.metadata.sorted_tables))


def _embed(doc_chunks) -> None:
    from app.services.llm import embed_texts

    texts = [d.chunk_text for d in doc_chunks]
    try:
        vectors = embed_texts(texts)
    except Exception as exc:  # noqa: BLE001
        log.warning("Embedding skipped (Ollama unavailable?): %s. Backfill via /ingest later.", exc)
        return
    for chunk, vec in zip(doc_chunks, vectors):
        chunk.embedding = vec
    log.info("Embedded %d document chunks.", len(vectors))


def _create_auth_users(db) -> None:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        log.info("Supabase service role not configured — skipping Auth user creation.")
        return
    try:
        from supabase import create_client

        from app.models.admin import User

        sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
        for name, email, _role in STAFF:
            try:
                res = sb.auth.admin.create_user(
                    {"email": email, "password": SEED_PASSWORD, "email_confirm": True}
                )
                uid = res.user.id if res and res.user else None
            except Exception as exc:  # noqa: BLE001 - user may already exist
                log.warning("Auth user %s: %s", email, exc)
                uid = None
            if uid:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    user.supabase_uid = uid
        db.commit()
        log.info("Supabase Auth users created (password: %s).", SEED_PASSWORD)
    except Exception as exc:  # noqa: BLE001
        log.warning("Auth user creation failed: %s", exc)


def _sync_graph(db) -> None:
    try:
        from app.services.graph.sync import sync_all

        sync_all(db)
        log.info("Neo4j graph synced.")
    except Exception as exc:  # noqa: BLE001
        log.warning("Graph sync skipped: %s", exc)


def main() -> int:
    log.info("Seeding Customer Intelligence Agent database…")
    _truncate_all()
    db = SessionLocal()
    try:
        seed_reference(db)
        db.flush()
        doc_chunks = seed_customers(db)
        _embed(doc_chunks)
        db.commit()

        from app.models.customer_data import Customer

        n = db.query(Customer).count()
        log.info("Seeded %d customers and %d document chunks.", n, len(doc_chunks))

        _create_auth_users(db)
        _sync_graph(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    log.info("Seed complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
