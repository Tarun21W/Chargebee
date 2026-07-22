"""Customer data endpoints (structured reads from Supabase Postgres)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.security import Principal, get_principal
from app.models.customer_data import Customer
from app.schemas.customer import CustomerBrief, CustomerDetail

router = APIRouter(prefix="/customers", tags=["customers"])


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
