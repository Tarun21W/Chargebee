"""Intent classification for the query router.

Routes each question to the cheapest capable path:
  structured -> facts-only answer (fast local model)
  rag        -> retrieval-augmented answer (primary model)
  reasoning  -> synthesis / why / what-if (heavy model, + risk + timeline)
  agent      -> multi-step, cross-team brief (multi-agent planner)
"""
from __future__ import annotations

from enum import Enum

from app.core.logging import get_logger
from app.services.llm import complete
from app.services.llm.prompts import INTENT_SYSTEM

log = get_logger("app.intent")

VALID = {"structured", "rag", "reasoning", "agent"}

# Fast keyword pre-filter avoids an LLM call for the obvious cases.
_AGENT_HINTS = ("prepare", "meeting", "brief", "agenda", "call prep", "qbr")
_REASON_HINTS = ("why", "should", "what if", "recommend", "risk", "churn")
_STRUCT_HINTS = ("how many", "when is", "what is the", "count", "total", "mrr", "renewal date")


class Intent(str, Enum):
    STRUCTURED = "structured"
    RAG = "rag"
    REASONING = "reasoning"
    AGENT = "agent"


def classify_intent(message: str) -> Intent:
    m = message.lower()
    if any(h in m for h in _AGENT_HINTS):
        return Intent.AGENT
    if any(h in m for h in _STRUCT_HINTS):
        return Intent.STRUCTURED
    if any(h in m for h in _REASON_HINTS):
        return Intent.REASONING

    # Fall back to the LLM classifier for ambiguous questions.
    try:
        raw = complete(
            f"{INTENT_SYSTEM}\n\nQuestion: {message}\nIntent:", tier="fast", max_tokens=4, temperature=0.0
        )
        token = raw.strip().lower().split()[0].strip(".,")
        if token in VALID:
            return Intent(token)
    except Exception as exc:  # noqa: BLE001
        log.debug("Intent LLM classify failed: %s", exc)
    return Intent.RAG
