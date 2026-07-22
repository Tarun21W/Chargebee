"""Analytics endpoints — cached aggregate reads for the overview dashboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.cache import TTLCache
from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.models.customer_data import Customer, Subscription, Ticket

router = APIRouter(prefix="/analytics", tags=["analytics"])

_overview_cache = TTLCache(ttl=30)


@router.get("/segments")
def segment_breakdown(
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("customer.read")),
) -> list[dict]:
    rows = db.execute(
        select(Customer.segment, func.count()).group_by(Customer.segment)
    ).all()
    return [{"segment": seg or "Unknown", "count": count} for seg, count in rows]


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("report.read")),
) -> dict:
    cached = _overview_cache.get("overview")
    if cached is not None:
        return cached

    segments = [
        {"label": s or "Unknown", "count": n}
        for s, n in db.execute(select(Customer.segment, func.count()).group_by(Customer.segment)).all()
    ]
    lifecycles = [
        {"label": s or "Unknown", "count": n}
        for s, n in db.execute(
            select(Customer.lifecycle_stage, func.count()).group_by(Customer.lifecycle_stage)
        ).all()
    ]
    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    total_mrr = float(db.scalar(select(func.coalesce(func.sum(Subscription.mrr), 0))) or 0)
    at_risk = db.scalar(
        select(func.count()).select_from(Customer).where(Customer.lifecycle_stage == "At-Risk")
    ) or 0
    past_due = db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.status == "past_due")
    ) or 0
    open_tickets = db.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.status == "open")
    ) or 0

    # Top at-risk accounts by MRR (for the "who to save first" list).
    top_rows = db.execute(
        select(Customer.customer_id, Customer.customer_name, Customer.segment, Subscription.mrr)
        .join(Subscription, Subscription.customer_id == Customer.customer_id)
        .where(Customer.lifecycle_stage == "At-Risk")
        .order_by(Subscription.mrr.desc())
        .limit(6)
    ).all()
    top_at_risk = [
        {"customer_id": str(cid), "customer_name": name, "segment": seg, "mrr": float(mrr or 0)}
        for cid, name, seg, mrr in top_rows
    ]

    result = {
        "total_customers": total_customers,
        "total_mrr": round(total_mrr, 2),
        "at_risk_count": at_risk,
        "past_due_count": past_due,
        "open_tickets": open_tickets,
        "segments": segments,
        "lifecycles": lifecycles,
        "top_at_risk": top_at_risk,
    }
    _overview_cache.set("overview", result)
    return result
