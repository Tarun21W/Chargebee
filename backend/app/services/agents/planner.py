"""Planner agent — orchestrates specialists into a single meeting brief.

Fans out to Support / Sales / Finance specialists (each blind to the others),
folds in the explainable risk score, then synthesises a business-ready brief:
overview, agenda, upsell, likely objections and a draft follow-up email.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.services.agents.specialists import finance_agent, sales_agent, support_agent
from app.services.facts import build_facts, facts_to_text
from app.services.llm import chat

PLANNER_SYSTEM = (
    "You are a customer planning agent preparing a rep for a customer meeting. Using the "
    "structured facts, the specialist notes and the risk assessment below, produce a concise, "
    "actionable brief with these sections:\n"
    "1. Overview (2-3 sentences)\n2. Suggested agenda (3-4 bullets)\n"
    "3. Upsell / expansion opportunity\n4. Likely objections and how to handle them\n"
    "5. Draft follow-up email (short)\n"
    "Use plain text with clear section headers. Do not invent facts."
)


def run_planner(db: Session, customer_id: uuid.UUID, request: str) -> str:
    facts = facts_to_text(build_facts(db, customer_id))

    support = support_agent(db, customer_id)
    sales = sales_agent(db, customer_id)
    finance = finance_agent(db, customer_id)

    from app.services.scoring import compute_risk

    risk = compute_risk(db, customer_id, persist=False)
    risk_text = (
        f"Health {risk['health_score']:.0f}, churn {risk['churn_score']:.0f}% "
        f"({risk['risk_level']}). {risk['explanation']}"
    )

    user = (
        f"REQUEST: {request}\n\n"
        f"FACTS:\n{facts}\n\n"
        f"SUPPORT NOTE:\n{support}\n\n"
        f"SALES NOTE:\n{sales}\n\n"
        f"FINANCE NOTE:\n{finance}\n\n"
        f"RISK:\n{risk_text}"
    )
    return chat(
        [{"role": "system", "content": PLANNER_SYSTEM}, {"role": "user", "content": user}],
        tier="heavy",
        temperature=0.3,
        max_tokens=1000,
    )
