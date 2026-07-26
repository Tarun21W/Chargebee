"""Ingest-on-create pipeline.

When a customer is added, this computes real ticket sentiment from the text via
the local LLM, embeds new documents into pgvector, adds the customer to the
Neo4j graph, and computes an initial risk score — so a single create call
populates every downstream feature.
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.customer_data import (
    Customer,
    DocChunk,
    Subscription,
    Ticket,
    TicketMessage,
)
from app.services.llm import complete, embed_texts

log = get_logger("app.ingestion")

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def compute_sentiment(text: str) -> float | None:
    """Classify message sentiment in [-1, 1] using the fast local model."""
    if not text or not text.strip():
        return None
    try:
        raw = complete(
            "Rate the sentiment of this customer message on a scale from -1.0 "
            "(very negative) to 1.0 (very positive). Reply with ONLY a number.\n\n"
            f"Message: {text}",
            tier="fast", temperature=0.0, max_tokens=8,
        )
        m = re.search(r"-?\d*\.?\d+", raw)
        return max(-1.0, min(1.0, float(m.group()))) if m else None
    except Exception as exc:  # noqa: BLE001 - never block ingest on sentiment
        log.warning("Sentiment computation failed: %s", exc)
        return None


def ingest_customer(
    db: Session,
    *,
    customer_name: str,
    segment: str | None = None,
    region: str | None = None,
    lifecycle_stage: str | None = "Active",
    email: str | None = None,
    subscription: dict | None = None,
    tickets: list[dict] | None = None,
    notes: list[str] | None = None,
    owner_user_id: uuid.UUID | None = None,
) -> dict:
    """Create a customer + related rows, then auto sentiment / embed / graph / risk."""
    customer = Customer(
        customer_name=customer_name, segment=segment, region=region,
        lifecycle_stage=lifecycle_stage, email=email, signup_date=date(2026, 7, 1),
        owner_user_id=owner_user_id,
    )
    db.add(customer)
    db.flush()
    cid = customer.customer_id

    if subscription:
        db.add(Subscription(
            customer_id=cid,
            plan=subscription.get("plan", "Pro"),
            mrr=subscription.get("mrr", 0),
            status=subscription.get("status", "active"),
            start_date=date(2026, 7, 1),
            renewal_date=subscription.get("renewal_date"),
        ))

    new_chunks: list[DocChunk] = []
    for t in tickets or []:
        body = t.get("body", "")
        sentiment = compute_sentiment(body)  # <-- real sentiment from the text
        ticket = Ticket(
            customer_id=cid, subject=t.get("subject", "(no subject)"),
            status=t.get("status", "open"), priority=t.get("priority", "medium"),
            sentiment=sentiment, opened_at=NOW,
        )
        db.add(ticket)
        db.flush()
        db.add(TicketMessage(
            ticket_id=ticket.ticket_id, sender="customer", body=body,
            sentiment=sentiment, created_at=NOW,
        ))
        new_chunks.append(DocChunk(
            customer_id=cid, source_type="ticket", source_id=str(ticket.ticket_id),
            chunk_text=f"[{ticket.subject}] Customer: {body}",
        ))

    for note in notes or []:
        new_chunks.append(DocChunk(customer_id=cid, source_type="note", chunk_text=note))

    db.add_all(new_chunks)
    db.flush()

    # Embed the new chunks (RAG)
    if new_chunks:
        try:
            vectors = embed_texts([c.chunk_text for c in new_chunks])
            for chunk, vec in zip(new_chunks, vectors):
                chunk.embedding = vec
        except Exception as exc:  # noqa: BLE001
            log.warning("Embedding new chunks failed: %s", exc)

    db.commit()

    # Add to the memory graph (incremental)
    try:
        from app.services.graph.sync import sync_customer
        sync_customer(db, cid)
    except Exception as exc:  # noqa: BLE001
        log.warning("Graph sync for new customer skipped: %s", exc)

    # Compute + persist an initial risk score
    risk = None
    try:
        from app.services.scoring import compute_risk
        risk = compute_risk(db, cid, persist=True)
    except Exception as exc:  # noqa: BLE001
        log.warning("Initial risk compute skipped: %s", exc)

    return {"customer_id": str(cid), "risk": risk}


def delete_customer(db: Session, customer_id: uuid.UUID) -> bool:
    """Delete a customer (DB cascades children) and remove it from the graph."""
    from sqlalchemy import delete as sqldelete

    customer = db.get(Customer, customer_id)
    if customer is None:
        return False
    # ON DELETE CASCADE on child FKs removes tickets/orders/doc_chunks/etc.
    db.execute(sqldelete(Customer).where(Customer.customer_id == customer_id))
    db.commit()

    try:
        from app.services.graph.sync import delete_customer_from_graph
        delete_customer_from_graph(customer_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("Graph delete skipped: %s", exc)

    from app.services.facts import invalidate_customer
    invalidate_customer(customer_id)
    return True
