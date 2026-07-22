"""Transparent, explainable health & churn scoring.

A weighted linear model over interpretable features. Because it is a weighted
sum, each feature's contribution to the churn score is exact and additive
(SHAP-style for a linear model), which powers the "why is this customer at
risk?" breakdown without any black-box approximation.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.risk import RiskFactor, Score, ScoringModel
from app.services.facts import build_facts

# feature key -> (display name, weight). Weights sum to 1.0.
WEIGHTS = {
    "usage_decline": ("Product usage declined", 0.25),
    "negative_sentiment": ("Negative support sentiment", 0.20),
    "payment": ("Payment / billing status", 0.15),
    "ticket_load": ("Open support tickets", 0.15),
    "login_recency": ("No recent logins", 0.15),
    "renewal": ("Renewal approaching", 0.10),
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _features(facts: dict) -> dict[str, float]:
    """Return each feature's risk value in [0, 1] (1 = maximally risky)."""
    act = facts["activity"]
    tick = facts["tickets"]
    sub = facts["subscription"]

    logins_30 = act["logins_last_30d"] or 0
    last_login = act["days_since_last_login"]
    avg_sent = tick["avg_sentiment"]
    open_tickets = tick["open"]
    status = (sub["status"] or "").lower()
    dtr = sub["days_to_renewal"]

    return {
        "usage_decline": _clamp(1 - logins_30 / 8.0),
        "negative_sentiment": (_clamp((0.2 - avg_sent) / 1.2) if avg_sent is not None else 0.2),
        "payment": 1.0 if status in ("past_due", "cancelled") else 0.0,
        "ticket_load": _clamp(open_tickets / 4.0),
        "login_recency": (_clamp((last_login - 3) / 30.0) if last_login is not None else 1.0),
        "renewal": (_clamp(1 - dtr / 90.0) if dtr is not None else 0.0),
    }


def _risk_level(churn: float) -> str:
    if churn >= 70:
        return "High"
    if churn >= 40:
        return "Medium"
    return "Low"


def compute_risk(db: Session, customer_id: uuid.UUID, persist: bool = True) -> dict:
    facts = build_facts(db, customer_id)
    feats = _features(facts)

    factors = []
    churn = 0.0
    for key, (display, weight) in WEIGHTS.items():
        contribution = weight * feats[key] * 100.0  # points toward churn (0..100*weight)
        churn += contribution
        factors.append(
            {"factor_name": display, "weight": weight, "contribution": round(contribution, 2)}
        )

    churn = round(churn, 2)
    health = round(100.0 - churn, 2)
    level = _risk_level(churn)
    factors.sort(key=lambda f: f["contribution"], reverse=True)

    explanation = _explain(factors, level)

    if persist:
        _persist(db, customer_id, health, churn, level, factors)

    return {
        "health_score": health,
        "churn_score": churn,
        "risk_level": level,
        "factors": factors,
        "explanation": explanation,
    }


def _explain(factors: list[dict], level: str) -> str:
    top = [f for f in factors if f["contribution"] > 1.0][:3]
    if not top:
        return "No significant risk signals — this customer looks healthy."
    drivers = ", ".join(f["factor_name"].lower() for f in top)
    return f"{level} churn risk, driven mainly by {drivers}."


def _persist(db: Session, customer_id, health, churn, level, factors) -> None:
    model = db.scalar(select(ScoringModel))
    model_id = model.model_id if model else None

    health_score = Score(
        customer_id=customer_id, model_id=model_id, score_type="health", value=health, risk_level=level
    )
    churn_score = Score(
        customer_id=customer_id, model_id=model_id, score_type="churn", value=churn, risk_level=level
    )
    db.add_all([health_score, churn_score])
    db.flush()
    for f in factors:
        db.add(
            RiskFactor(
                score_id=churn_score.score_id,
                factor_name=f["factor_name"],
                weight=f["weight"],
                contribution=f["contribution"],
            )
        )
    db.commit()
