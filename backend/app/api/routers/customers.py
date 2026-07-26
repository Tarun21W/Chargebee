"""Customer data endpoints (structured reads from Supabase Postgres)."""
from __future__ import annotations

import uuid

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import write_audit
from app.core.db import get_db
from app.core.security import Principal, get_principal, require_permission
from app.models.customer_data import Customer
from app.schemas.customer import CustomerBrief, CustomerDetail
from app.services.ingestion.pipeline import delete_customer, ingest_customer

router = APIRouter(prefix="/customers", tags=["customers"])


class NewTicket(BaseModel):
    subject: str
    body: str  # customer's message — sentiment is computed from this
    status: str = "open"
    priority: str = "medium"


class NewSubscription(BaseModel):
    plan: str = "Pro"
    mrr: float = 0
    status: str = "active"
    renewal_date: date | None = None


class NewCustomer(BaseModel):
    customer_name: str
    segment: str | None = None
    region: str | None = None
    lifecycle_stage: str | None = "Active"
    email: str | None = None
    subscription: NewSubscription | None = None
    tickets: list[NewTicket] = []
    notes: list[str] = []


@router.post("", status_code=201)
def create_customer(
    body: NewCustomer,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission("customer.read")),
) -> dict:
    """Create a customer and auto-run sentiment + embeddings + graph + risk."""
    import uuid as _uuid

    result = ingest_customer(
        db,
        customer_name=body.customer_name,
        segment=body.segment,
        region=body.region,
        lifecycle_stage=body.lifecycle_stage,
        email=body.email,
        subscription=body.subscription.model_dump() if body.subscription else None,
        tickets=[t.model_dump() for t in body.tickets],
        notes=body.notes,
        owner_user_id=_uuid.UUID(principal.user_id) if principal.user_id else None,
    )
    write_audit(
        db,
        _uuid.UUID(principal.user_id) if principal.user_id else None,
        "customer.create", "customer", result["customer_id"],
    )
    return result


@router.get("", response_model=list[CustomerBrief])
def list_customers(
    segment: str | None = Query(default=None),
    lifecycle_stage: str | None = Query(default=None),
    q: str | None = Query(default=None, description="name search"),
    db: Session = Depends(get_db),
    _: Principal = Depends(get_principal),
) -> list[Customer]:
    stmt = select(Customer)
    if segment:
        stmt = stmt.where(Customer.segment == segment)
    if lifecycle_stage:
        stmt = stmt.where(Customer.lifecycle_stage == lifecycle_stage)
    if q:
        stmt = stmt.where(Customer.customer_name.ilike(f"%{q}%"))
    stmt = stmt.order_by(Customer.customer_name).limit(200)
    return list(db.scalars(stmt).all())


@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Principal = Depends(get_principal),
) -> Customer:
    stmt = (
        select(Customer)
        .where(Customer.customer_id == customer_id)
        .options(
            selectinload(Customer.tickets),
            selectinload(Customer.orders),
            selectinload(Customer.subscriptions),
            selectinload(Customer.interactions),
        )
    )
    customer = db.scalar(stmt)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}")
def remove_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission("admin.manage")),
) -> dict:
    """Delete a customer (children cascade) and remove it from the graph."""
    ok = delete_customer(db, customer_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Customer not found")
    import uuid as _uuid

    write_audit(
        db,
        _uuid.UUID(principal.user_id) if principal.user_id else None,
        "customer.delete", "customer", str(customer_id),
    )
    return {"deleted": str(customer_id)}
