"""Multi-agent endpoints — the 'prepare for the meeting' brief."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.services.agents.planner import run_planner

router = APIRouter(prefix="/customers", tags=["agents"])


class BriefRequest(BaseModel):
    request: str = "Prepare me for a meeting with this customer."


@router.post("/{customer_id}/brief")
def meeting_brief(
    customer_id: uuid.UUID,
    body: BriefRequest,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("assistant.chat")),
) -> dict:
    brief = run_planner(db, customer_id, body.request)
    return {"customer_id": str(customer_id), "brief": brief}
