"""Customer summary endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.models.summary import Summary
from app.schemas.summary import SummaryOut, SummaryRequest
from app.services.summary import generate_summary

router = APIRouter(prefix="/customers", tags=["summary"])


@router.post("/{customer_id}/summary", response_model=SummaryOut)
def create_summary(
    customer_id: uuid.UUID,
    body: SummaryRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission("summary.generate")),
) -> Summary:
    user_id = uuid.UUID(principal.user_id) if principal.user_id else None
    summary = generate_summary(db, customer_id, team=body.team, user_id=user_id)
    write_audit(db, user_id, "summary.generate", "customer", str(customer_id))
    return summary


@router.get("/{customer_id}/summary/latest", response_model=SummaryOut | None)
def latest_summary(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("summary.generate")),
) -> Summary | None:
    return db.scalar(
        select(Summary)
        .where(Summary.customer_id == customer_id)
        .order_by(Summary.generated_date.desc())
    )
