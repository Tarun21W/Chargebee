"""ML churn scoring with SHAP explanations.

Loads the trained artifact (see train.py), predicts churn probability for a
customer, and attributes the prediction to per-feature **SHAP** contributions —
the same additive "why?" breakdown the UI renders, but now learned, not hand-set.

Returns the exact same dict shape as the formula scorer so the API/UI are
unchanged, and degrades gracefully if the artifact or SHAP is unavailable.
"""
from __future__ import annotations

import os
import uuid

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.facts import build_facts
from app.services.scoring.scorer import WEIGHTS, _explain, _features, _persist, _risk_level

log = get_logger("app.scoring.ml")

ARTIFACT = os.path.join(os.path.dirname(__file__), "churn_model.joblib")
_MODEL: dict | None = None


def available() -> bool:
    return os.path.exists(ARTIFACT)


def _load() -> dict:
    global _MODEL
    if _MODEL is None:
        _MODEL = joblib.load(ARTIFACT)
    return _MODEL


def _shap_contributions(art: dict, x: np.ndarray, churn_prob: float) -> np.ndarray:
    """Per-feature contribution to churn probability, in percentage points.

    For the tree model we use SHAP's probability output (contributions are exact
    and additive). Falls back to a model-agnostic estimate if SHAP fails.
    """
    try:
        import shap

        if art["kind"] == "gb":
            explainer = shap.TreeExplainer(
                art["model"], data=art["background"],
                model_output="probability", feature_perturbation="interventional",
            )
            vals = explainer.shap_values(x)
            vals = vals[1] if isinstance(vals, list) else vals
            return np.asarray(vals, dtype=float).reshape(-1) * 100.0

        explainer = shap.LinearExplainer(art["model"], art["background"])
        vals = np.asarray(explainer.shap_values(x), dtype=float).reshape(-1)
        # LinearExplainer works in log-odds space; rescale so contributions sum
        # to (churn - baseline) in percentage points for an additive display.
        base = float(art["model"].predict_proba(art["background"]).mean(axis=0)[1]) * 100.0
        target = churn_prob * 100.0 - base
        total = vals.sum()
        return vals * (target / total) if abs(total) > 1e-9 else vals
    except Exception as exc:  # noqa: BLE001 - explanation must never break scoring
        log.warning("SHAP unavailable (%s); using weighted-feature fallback.", exc)
        feats = np.asarray([x[0][i] for i in range(x.shape[1])])
        weights = np.asarray([WEIGHTS[k][1] for k in art["features"]])
        return feats * weights * 100.0


def compute_risk_ml(db: Session, customer_id: uuid.UUID, persist: bool = True) -> dict:
    art = _load()
    facts = build_facts(db, customer_id)
    feats = _features(facts)

    names = art["features"]
    x = np.array([[feats[n] for n in names]], dtype=float)

    churn_prob = float(art["model"].predict_proba(x)[0, 1])
    churn = round(churn_prob * 100.0, 2)
    health = round(100.0 - churn, 2)
    level = _risk_level(churn)

    contribs = _shap_contributions(art, x, churn_prob)
    factors = [
        {"factor_name": WEIGHTS[name][0], "weight": WEIGHTS[name][1], "contribution": round(float(c), 2)}
        for name, c in zip(names, contribs)
    ]
    factors.sort(key=lambda f: f["contribution"], reverse=True)

    explanation = _explain(factors, level) + f"  (ML model · AUC {art.get('auc', 0):.2f})"

    if persist:
        _persist(db, customer_id, health, churn, level, factors)

    return {
        "health_score": health,
        "churn_score": churn,
        "risk_level": level,
        "factors": factors,
        "explanation": explanation,
    }
