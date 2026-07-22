"""Customer 360 timeline endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.services.timeline import build_timeline

router = APIRouter(prefix="/customers", tags=["timeline"])


@router.get("/{customer_id}/timeline")
def get_timeline(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("customer.read")),
) -> list[dict]:
    return build_timeline(db, customer_id)
