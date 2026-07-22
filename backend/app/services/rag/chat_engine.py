"""Conversational RAG assistant with persisted history and citations.

Grounds every answer in (a) structured customer facts and (b) retrieved
documents. When the question is about risk/churn, the current explainable risk
breakdown is folded into the context so 'why is this customer at risk?' is
answered from real signals.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.assistant import AssistantConfig, Conversation, Message
from app.services.facts import NOW, build_facts, facts_to_text
from app.services.llm import chat
from app.services.llm.prompts import CHAT_SYSTEM
from app.services.rag import retrieve

log = get_logger("app.chat")

RISK_KEYWORDS = ("risk", "churn", "at-risk", "at risk", "leave", "cancel", "retention")


def _get_or_create_conversation(
    db: Session, customer_id: uuid.UUID, conversation_id: uuid.UUID | None, user_id: uuid.UUID | None
) -> Conversation:
    if conversation_id:
        conv = db.get(Conversation, conversation_id)
        if conv:
            return conv
    assistant = db.scalar(select(AssistantConfig))
    conv = Conversation(
        customer_id=customer_id,
        user_id=user_id,
        assistant_id=assistant.assistant_id if assistant else None,
    )
    db.add(conv)
    db.flush()
    return conv


def _risk_context(db: Session, customer_id: uuid.UUID) -> str:
    """Lazy import of the scoring service to avoid a hard dependency cycle."""
    try:
        from app.services.scoring import compute_risk

        risk = compute_risk(db, customer_id, persist=False)
        factors = "; ".join(
            f"{f['factor_name']} ({f['contribution']:+.1f})" for f in risk["factors"]
        )
        return (
            f"\n\nRISK: health={risk['health_score']:.0f}, churn={risk['churn_score']:.0f}%, "
            f"level={risk['risk_level']}. Factors: {factors}"
        )
    except Exception as exc:  # noqa: BLE001
        log.debug("Risk context unavailable: %s", exc)
        return ""


def answer(
    db: Session,
    customer_id: uuid.UUID,
    message: str,
    conversation_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> dict:
    conv = _get_or_create_conversation(db, customer_id, conversation_id, user_id)
    assistant = db.get(AssistantConfig, conv.assistant_id) if conv.assistant_id else None
    ctx_limit = assistant.context_limit if assistant else 10
    assistant_name = assistant.assistant_name if assistant else "Assistant"

    # Route the query: pick model tier and how much context to assemble.
    from app.services.agents import Intent, classify_intent

    intent = classify_intent(message)
    tier = {
        Intent.STRUCTURED: "fast",
        Intent.RAG: "primary",
        Intent.REASONING: "heavy",
        Intent.AGENT: "heavy",
    }[intent]

    facts_text = facts_to_text(build_facts(db, customer_id))
    if intent in (Intent.REASONING, Intent.AGENT) or any(k in message.lower() for k in RISK_KEYWORDS):
        facts_text += _risk_context(db, customer_id)
    if intent in (Intent.REASONING, Intent.AGENT):
        from app.services.timeline import build_timeline, timeline_to_text

        facts_text += "\n\nTIMELINE:\n" + timeline_to_text(build_timeline(db, customer_id))

    # Agent-plan questions are handled by the multi-agent planner when available.
    if intent == Intent.AGENT:
        planned = _try_planner(db, customer_id, message)
        if planned is not None:
            return _persist_and_return(db, conv, message, planned, [], intent.value)

    k = 3 if intent == Intent.STRUCTURED else 6
    chunks = retrieve(db, customer_id, message, k=k)
    context_text = "\n---\n".join(c["chunk_text"] for c in chunks) or "(no documents retrieved)"
    citations = [
        {"source_type": c["source_type"], "source_id": c["source_id"], "snippet": c["chunk_text"][:160]}
        for c in chunks
    ]

    # Prior turns (most recent N), oldest first.
    history = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conv.conversation_id)
            .order_by(Message.created_at.desc())
            .limit(ctx_limit)
        ).all()
    )[::-1]

    messages = [
        {
            "role": "system",
            "content": CHAT_SYSTEM.format(
                assistant_name=assistant_name, facts=facts_text, context=context_text
            ),
        }
    ]
    messages += [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": message})

    reply = chat(messages, tier=tier, temperature=0.3, max_tokens=800)
    return _persist_and_return(db, conv, message, reply, citations, intent.value)


def _try_planner(db: Session, customer_id: uuid.UUID, message: str) -> str | None:
    """Delegate multi-step 'brief' questions to the planner if it's available."""
    try:
        from app.services.agents.planner import run_planner

        return run_planner(db, customer_id, message)
    except Exception as exc:  # noqa: BLE001
        log.debug("Planner unavailable, falling back to chat: %s", exc)
        return None


def _persist_and_return(
    db: Session, conv: Conversation, message: str, reply: str, citations: list, intent: str
) -> dict:
    db.add(Message(conversation_id=conv.conversation_id, role="user", content=message, citations=[]))
    db.add(
        Message(
            conversation_id=conv.conversation_id, role="assistant", content=reply, citations=citations
        )
    )
    conv.last_active_at = NOW
    db.commit()
    return {
        "conversation_id": str(conv.conversation_id),
        "answer": reply,
        "citations": citations,
        "intent": intent,
    }
