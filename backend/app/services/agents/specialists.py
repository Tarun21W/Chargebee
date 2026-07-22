"""Specialist agents — each reasons over ONLY its own data slice.

Keeping each agent's view narrow mirrors how real teams operate and keeps
prompts focused. The planner composes their outputs.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_data import Order, Subscription, Ticket
from app.services.llm import chat


def support_agent(db: Session, customer_id: uuid.UUID) -> str:
    tickets = list(db.scalars(select(Ticket).where(Ticket.customer_id == customer_id)).all())
    open_t = [t for t in tickets if t.status == "open"]
    lines = [
        f"- {t.subject} (priority={t.priority}, sentiment={t.sentiment}, status={t.status})"
        for t in sorted(tickets, key=lambda x: (x.sentiment or 0))[:6]
    ]
    data = f"{len(tickets)} tickets, {len(open_t)} open.\n" + "\n".join(lines)
    return chat(
        [
            {"role": "system", "content": "You are a Support specialist. In 2-3 sentences, summarise this customer's support health and any unresolved risks. Use only the data."},
            {"role": "user", "content": data},
        ],
        tier="fast",
        max_tokens=200,
    )


def sales_agent(db: Session, customer_id: uuid.UUID) -> str:
    orders = list(db.scalars(select(Order).where(Order.customer_id == customer_id)).all())
    sub = db.scalar(select(Subscription).where(Subscription.customer_id == customer_id))
    total = sum(float(o.total_amount) for o in orders)
    data = (
        f"Plan={sub.plan if sub else 'none'}, MRR=${float(sub.mrr) if sub else 0}/mo. "
        f"{len(orders)} orders totalling ${total:,.0f}."
    )
    return chat(
        [
            {"role": "system", "content": "You are a Sales specialist. In 2-3 sentences, identify expansion/upsell potential and account value. Use only the data."},
            {"role": "user", "content": data},
        ],
        tier="fast",
        max_tokens=200,
    )


def finance_agent(db: Session, customer_id: uuid.UUID) -> str:
    sub = db.scalar(select(Subscription).where(Subscription.customer_id == customer_id))
    if not sub:
        return "No active subscription on record."
    data = (
        f"Plan={sub.plan}, MRR=${float(sub.mrr)}/mo, status={sub.status}, "
        f"renewal={sub.renewal_date}."
    )
    return chat(
        [
            {"role": "system", "content": "You are a Finance specialist. In 1-2 sentences, flag billing/renewal risks. Use only the data."},
            {"role": "user", "content": data},
        ],
        tier="fast",
        max_tokens=150,
    )
