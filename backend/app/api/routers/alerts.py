"""Alerts endpoints — thin engine over real tables (evaluate risk -> alerts)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.models.alerts import Alert, AlertRule
from app.models.customer_data import Customer
from app.services.scoring import compute_risk

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("customer.read")),
) -> list[dict]:
    rows = db.scalars(select(Alert).order_by(Alert.fired_at.desc()).limit(200)).all()
    return [
        {
            "alert_id": str(a.alert_id),
            "customer_id": str(a.customer_id),
            "alert_type": a.alert_type,
            "severity": a.severity,
            "alert_status": a.alert_status,
            "fired_at": a.fired_at,
        }
        for a in rows
    ]


@router.post("/evaluate")
def evaluate_alerts(
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("alert.manage")),
) -> dict:
    """Score every customer and raise a high-churn alert where one isn't already open."""
    rule = db.scalar(select(AlertRule).where(AlertRule.rule_name == "Churn risk high"))
    created = 0
    for customer in db.scalars(select(Customer)).all():
        risk = compute_risk(db, customer.customer_id, persist=False)
        if risk["risk_level"] != "High":
            continue
        existing = db.scalar(
            select(Alert).where(
                Alert.customer_id == customer.customer_id,
                Alert.alert_type == "churn_risk",
                Alert.alert_status == "open",
            )
        )
        if existing:
            continue
        db.add(
            Alert(
                rule_id=rule.rule_id if rule else None,
                customer_id=customer.customer_id,
                alert_type="churn_risk",
                alert_status="open",
                severity="high",
            )
        )
        created += 1
    db.commit()
    return {"alerts_created": created}
