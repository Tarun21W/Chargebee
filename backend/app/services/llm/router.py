"""LLM routing via LiteLLM — local Ollama only (no cloud).

Task tiers pick the model:
  - "fast"    -> small model (qwen2.5:3b): intent classification, query rewrite
  - "primary" -> quality model (qwen2.5:7b): chat, RAG answers
  - "heavy"   -> quality model (qwen2.5:7b): summaries, agents, reasoning
"""
from __future__ import annotations

import litellm

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("app.llm")

litellm.drop_params = True  # ignore params a provider doesn't support

_TIER_MODEL = {
    "fast": settings.llm_fast_model,
    "primary": settings.llm_primary_model,
    "heavy": settings.llm_heavy_model,
}


def _kwargs(model: str) -> dict:
    return {
        "model": f"ollama/{model}",
        "api_base": settings.ollama_base_url,
        "timeout": settings.llm_request_timeout,
    }


def chat(
    messages: list[dict],
    tier: str = "primary",
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """Return the assistant text for a chat-style message list (local Ollama)."""
    model = _TIER_MODEL.get(tier, settings.llm_primary_model)
    resp = litellm.completion(
        **_kwargs(model), messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return resp["choices"][0]["message"]["content"] or ""


def complete(prompt: str, tier: str = "primary", **kwargs) -> str:
    """Convenience wrapper for a single user prompt."""
    return chat([{"role": "user", "content": prompt}], tier=tier, **kwargs)
