"""Risk & health scoring endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.services.scoring import compute_risk

router = APIRouter(prefix="/customers", tags=["risk"])


@router.get("/{customer_id}/risk")
def get_risk(
    customer_id: uuid.UUID,
    persist: bool = Query(default=True, description="store a Score snapshot"),
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("risk.read")),
) -> dict:
    return compute_risk(db, customer_id, persist=persist)
