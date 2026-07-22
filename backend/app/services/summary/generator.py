"""AI customer summary generation — template-driven, sectioned, with citations."""
from __future__ import annotations

import json
import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.summary import Summary, SummarySection, SummaryTemplate
from app.services.facts import build_facts, facts_to_text
from app.services.llm import chat
from app.services.llm.prompts import SUMMARY_SYSTEM, SUMMARY_USER
from app.services.rag import retrieve

log = get_logger("app.summary")

DEFAULT_SECTIONS = ["Activity", "Issues", "Insights", "Recommendations"]


def _extract_json(raw: str) -> dict | None:
    """Best-effort extraction of a JSON object from an LLM response."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _confidence(facts: dict, n_context: int) -> float:
    """Data-coverage heuristic: more signals + retrieved context => higher confidence."""
    signals = [
        facts["subscription"]["plan"],
        facts["subscription"]["status"],
        facts["tickets"]["avg_sentiment"] is not None,
        facts["orders"]["count"] > 0,
        facts["activity"]["days_since_last_login"] is not None,
    ]
    coverage = sum(1 for s in signals if s) / len(signals)
    context_bonus = 0.15 if n_context > 0 else 0.0
    return round(min(0.95, 0.45 + 0.4 * coverage + context_bonus), 3)


def generate_summary(
    db: Session, customer_id: uuid.UUID, team: str = "CustomerSuccess", user_id: uuid.UUID | None = None
) -> Summary:
    facts = build_facts(db, customer_id)
    facts_text = facts_to_text(facts)

    # Retrieve supporting context (complaints, notes) for Issues/Insights.
    context_chunks = retrieve(db, customer_id, "issues complaints risks insights recent activity", k=6)
    docs_text = "\n---\n".join(c["chunk_text"] for c in context_chunks) or "(no documents retrieved)"
    citations = [{"source_type": c["source_type"], "source_id": c["source_id"]} for c in context_chunks]

    # Chronological context grounds the "Activity" section.
    from app.services.timeline import build_timeline, timeline_to_text

    timeline_text = timeline_to_text(build_timeline(db, customer_id))
    context_text = f"RECENT TIMELINE:\n{timeline_text}\n\nDOCUMENTS:\n{docs_text}"

    template = db.scalar(select(SummaryTemplate).where(SummaryTemplate.team == team))

    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM.format(team=team)},
        {"role": "user", "content": SUMMARY_USER.format(facts=facts_text, context=context_text)},
    ]
    raw = chat(messages, tier="heavy", temperature=0.2, max_tokens=1200)
    parsed = _extract_json(raw)

    sections_data: list[dict]
    if parsed and isinstance(parsed.get("sections"), list):
        sections_data = parsed["sections"]
    else:
        # Fallback: put the whole response into a single section so nothing is lost.
        log.warning("Summary JSON parse failed; using raw text fallback.")
        sections_data = [{"section_name": "Summary", "content": raw.strip()}]

    confidence = _confidence(facts, len(context_chunks))

    summary = Summary(
        customer_id=customer_id,
        template_id=template.template_id if template else None,
        summary_type=team,
        confidence_level=confidence,
        body=raw,
        generated_by=user_id,
    )
    db.add(summary)
    db.flush()

    for i, sec in enumerate(sections_data):
        db.add(
            SummarySection(
                summary_id=summary.summary_id,
                section_name=sec.get("section_name", f"Section {i + 1}"),
                display_order=i,
                content=sec.get("content", ""),
                # Citations are most relevant to evidence-bearing sections.
                citations=citations if sec.get("section_name") in ("Issues", "Insights") else [],
            )
        )
    db.commit()
    db.refresh(summary)
    return summary
