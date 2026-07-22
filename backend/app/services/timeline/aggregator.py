"""Customer 360 timeline — a unified chronological event feed.

Merges dated events across tickets, orders, subscriptions, notable
interactions and score snapshots into a single sorted stream. Also used as
chronological context for the summary and chat prompts.
"""
from __future__ import annotations

import uuid
from datetime import datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import TTLCache
from app.models.customer_data import Interaction, Order, Subscription, Ticket
from app.models.risk import Score

_timeline_cache = TTLCache(ttl=60)


def _as_dt(value) -> datetime:
    """Normalise date/datetime to an aware datetime for sorting."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def build_timeline(db: Session, customer_id: uuid.UUID, limit: int = 60) -> list[dict]:
    cache_key = f"{customer_id}:{limit}"
    cached = _timeline_cache.get(cache_key)
    if cached is not None:
        return cached

    events: list[dict] = []

    for t in db.scalars(select(Ticket).where(Ticket.customer_id == customer_id)).all():
        sent = float(t.sentiment) if t.sentiment is not None else None
        events.append(
            {
                "date": _as_dt(t.opened_at),
                "category": "sentiment" if (sent is not None and sent < -0.2) else "ticket",
                "title": f"Ticket opened: {t.subject}",
                "detail": f"priority={t.priority}, status={t.status}"
                + (f", sentiment={sent:+.2f}" if sent is not None else ""),
                "sentiment": sent,
            }
        )
        if t.closed_at:
            events.append(
                {
                    "date": _as_dt(t.closed_at),
                    "category": "ticket",
                    "title": f"Ticket closed: {t.subject}",
                    "detail": None,
                    "sentiment": None,
                }
            )

    for o in db.scalars(select(Order).where(Order.customer_id == customer_id)).all():
        events.append(
            {
                "date": _as_dt(o.order_date),
                "category": "order",
                "title": f"Order placed — ${float(o.total_amount):,.0f}",
                "detail": f"status={o.status}",
                "sentiment": None,
            }
        )

    for s in db.scalars(select(Subscription).where(Subscription.customer_id == customer_id)).all():
        if s.start_date:
            events.append(
                {
                    "date": _as_dt(s.start_date),
                    "category": "subscription",
                    "title": f"Subscribed to {s.plan} (${float(s.mrr):,.0f}/mo)",
                    "detail": None,
                    "sentiment": None,
                }
            )
        if s.renewal_date:
            events.append(
                {
                    "date": _as_dt(s.renewal_date),
                    "category": "subscription",
                    "title": f"Renewal due — {s.plan}",
                    "detail": f"status={s.status}",
                    "sentiment": None,
                }
            )

    # Notable interactions only (skip routine logins to keep the feed readable).
    notable = db.scalars(
        select(Interaction).where(
            Interaction.customer_id == customer_id, Interaction.type != "login"
        )
    ).all()
    for i in notable:
        events.append(
            {
                "date": _as_dt(i.occurred_at),
                "category": "interaction",
                "title": f"{i.type.replace('_', ' ').title()}",
                "detail": (i.meta or {}).get("feature") if i.meta else None,
                "sentiment": None,
            }
        )

    for sc in db.scalars(
        select(Score).where(Score.customer_id == customer_id, Score.score_type == "churn")
    ).all():
        events.append(
            {
                "date": _as_dt(sc.computed_at),
                "category": "score",
                "title": f"Churn score {float(sc.value):.0f}% ({sc.risk_level})",
                "detail": None,
                "sentiment": None,
            }
        )

    events.sort(key=lambda e: e["date"], reverse=True)
    result = events[:limit]
    _timeline_cache.set(cache_key, result)
    return result


def timeline_to_text(events: list[dict], limit: int = 15) -> str:
    lines = [
        f"{e['date'].date().isoformat()} — {e['title']}" for e in events[:limit]
    ]
    return "\n".join(lines)
