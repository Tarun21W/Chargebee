"""Assemble structured, factual signals about a customer for LLM prompts.

Shared by summary generation, the chat assistant and the agents so every AI
surface reasons from the same ground truth.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.cache import TTLCache
from app.models.customer_data import Customer, Interaction, Order, Subscription, Ticket

TODAY = date(2026, 7, 17)
NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)

# Facts are read by summary, chat, risk and agents — cache briefly to avoid
# recomputing the same aggregates across a burst of requests.
_facts_cache = TTLCache(ttl=60)


def invalidate_customer(customer_id: uuid.UUID) -> None:
    _facts_cache.invalidate(str(customer_id))


def build_facts(db: Session, customer_id: uuid.UUID) -> dict:
    cached = _facts_cache.get(str(customer_id))
    if cached is not None:
        return cached

    c = db.get(Customer, customer_id)
    if c is None:
        raise ValueError("Customer not found")

    # Subscription (most recent)
    sub = db.scalar(
        select(Subscription)
        .where(Subscription.customer_id == customer_id)
        .order_by(Subscription.start_date.desc())
    )
    days_to_renewal = None
    if sub and sub.renewal_date:
        days_to_renewal = (sub.renewal_date - TODAY).days

    # Tickets
    tickets = list(db.scalars(select(Ticket).where(Ticket.customer_id == customer_id)).all())
    open_tickets = [t for t in tickets if t.status == "open"]
    sentiments = [float(t.sentiment) for t in tickets if t.sentiment is not None]
    avg_sentiment = round(sum(sentiments) / len(sentiments), 3) if sentiments else None
    negative_subjects = [t.subject for t in tickets if (t.sentiment or 0) < -0.2][:5]

    # Orders
    order_rows = list(db.scalars(select(Order).where(Order.customer_id == customer_id)).all())
    total_spend = round(sum(float(o.total_amount) for o in order_rows), 2)
    last_order = max((o.order_date for o in order_rows), default=None)

    # Activity — logins in last 30 / 90 days, days since last login
    logins = list(
        db.scalars(
            select(Interaction.occurred_at).where(
                Interaction.customer_id == customer_id, Interaction.type == "login"
            )
        ).all()
    )
    days_since = [(NOW - lg).days for lg in logins]
    logins_30 = sum(1 for d in days_since if d <= 30)
    logins_90 = sum(1 for d in days_since if d <= 90)
    last_login_days = min(days_since) if days_since else None

    result = {
        "profile": {
            "name": c.customer_name,
            "segment": c.segment,
            "region": c.region,
            "lifecycle_stage": c.lifecycle_stage,
            "signup_date": c.signup_date.isoformat() if c.signup_date else None,
        },
        "subscription": {
            "plan": sub.plan if sub else None,
            "mrr": float(sub.mrr) if sub else None,
            "status": sub.status if sub else None,
            "renewal_date": sub.renewal_date.isoformat() if sub and sub.renewal_date else None,
            "days_to_renewal": days_to_renewal,
        },
        "tickets": {
            "total": len(tickets),
            "open": len(open_tickets),
            "avg_sentiment": avg_sentiment,
            "negative_subjects": negative_subjects,
        },
        "orders": {
            "count": len(order_rows),
            "total_spend": total_spend,
            "last_order_date": last_order.isoformat() if last_order else None,
        },
        "activity": {
            "logins_last_30d": logins_30,
            "logins_last_90d": logins_90,
            "days_since_last_login": last_login_days,
        },
    }
    _facts_cache.set(str(customer_id), result)
    return result


def facts_to_text(facts: dict) -> str:
    p, s, t, o, a = (
        facts["profile"],
        facts["subscription"],
        facts["tickets"],
        facts["orders"],
        facts["activity"],
    )
    lines = [
        f"Name: {p['name']} | Segment: {p['segment']} | Region: {p['region']} | "
        f"Lifecycle: {p['lifecycle_stage']} | Customer since: {p['signup_date']}",
        f"Subscription: {s['plan']} at ${s['mrr']}/mo | status={s['status']} | "
        f"renews {s['renewal_date']} (in {s['days_to_renewal']} days)",
        f"Tickets: {t['total']} total, {t['open']} open, avg sentiment {t['avg_sentiment']}",
    ]
    if t["negative_subjects"]:
        lines.append("Recent complaints: " + "; ".join(t["negative_subjects"]))
    lines.append(
        f"Orders: {o['count']} orders, ${o['total_spend']} total spend, last on {o['last_order_date']}"
    )
    lines.append(
        f"Activity: {a['logins_last_30d']} logins in 30d, {a['logins_last_90d']} in 90d, "
        f"last login {a['days_since_last_login']} days ago"
    )
    return "\n".join(lines)
