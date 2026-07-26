"""Train the churn-risk ML model.

Run:  python -m app.services.scoring.train

We don't yet have real labeled churn history, so we synthesise a labeled
training set over the SAME six features the production scorer extracts, using a
known generative rule + noise. A gradient-boosting classifier (and a logistic
regression baseline) is trained; the better one by held-out AUC is saved. At
inference we explain each prediction with SHAP (see ml_scorer.py).

Swap `_synthetic_dataset()` for real (features, churned) rows when available and
retrain — nothing else changes.
"""
from __future__ import annotations

import os

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from app.core.logging import configure_logging, get_logger
from app.services.scoring.scorer import WEIGHTS

configure_logging()
log = get_logger("app.scoring.train")

FEATURES = list(WEIGHTS.keys())  # usage_decline, negative_sentiment, payment, ticket_load, login_recency, renewal
ARTIFACT = os.path.join(os.path.dirname(__file__), "churn_model.joblib")


def _synthetic_dataset(n: int = 5000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Features in [0,1] (same space as production) + a churn label."""
    rng = np.random.default_rng(seed)
    X = rng.random((n, len(FEATURES)))
    # "True" latent churn drivers (order matches FEATURES). Payment problems and
    # usage decline weigh most; renewal proximity least.
    true_w = np.array([2.4, 1.9, 2.7, 1.4, 1.5, 1.0])
    logit = X @ true_w - 3.4 + rng.normal(0, 0.6, n)
    p = 1.0 / (1.0 + np.exp(-logit))
    y = (rng.random(n) < p).astype(int)
    return X, y


def main() -> int:
    X, y = _synthetic_dataset()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=0, stratify=y)

    gb = GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=0)
    gb.fit(X_tr, y_tr)
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_tr, y_tr)

    auc_gb = roc_auc_score(y_te, gb.predict_proba(X_te)[:, 1])
    auc_lr = roc_auc_score(y_te, lr.predict_proba(X_te)[:, 1])
    log.info("Held-out AUC — gradient boosting: %.3f · logistic regression: %.3f", auc_gb, auc_lr)

    if auc_gb >= auc_lr:
        model, kind, auc = gb, "gb", auc_gb
    else:
        model, kind, auc = lr, "lr", auc_lr

    # Background sample for SHAP (expected-value baseline).
    idx = np.random.default_rng(1).choice(len(X_tr), size=200, replace=False)
    background = X_tr[idx]

    joblib.dump(
        {"model": model, "kind": kind, "features": FEATURES, "background": background, "auc": float(auc)},
        ARTIFACT,
    )
    log.info("Saved %s model (AUC %.3f) -> %s", kind, auc, ARTIFACT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
