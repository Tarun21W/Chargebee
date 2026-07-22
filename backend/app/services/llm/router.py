"""LLM routing via LiteLLM: local Ollama primary with Hugging Face fallback.

Task tiers map to models:
  - "fast"   -> small/primary local model (classification, query rewrite)
  - "primary"-> primary local model (chat, RAG answers)
  - "heavy"  -> larger local model (summaries, reasoning)
On any local error/timeout, we transparently fall back to a Hugging Face
Inference model so the API stays responsive when Ollama is cold or slow.
"""
from __future__ import annotations

import litellm

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("app.llm")

litellm.drop_params = True  # ignore params a provider doesn't support

_TIER_MODEL = {
    "fast": settings.llm_primary_model,
    "primary": settings.llm_primary_model,
    "heavy": settings.llm_heavy_model,
}


def _local_kwargs(model: str) -> dict:
    return {
        "model": f"ollama/{model}",
        "api_base": settings.ollama_base_url,
        "timeout": settings.llm_request_timeout,
    }


def _fallback_kwargs() -> dict | None:
    if not settings.hf_token:
        return None
    return {
        "model": f"huggingface/{settings.hf_fallback_model}",
        "api_key": settings.hf_token,
        "timeout": settings.llm_request_timeout,
    }


def chat(
    messages: list[dict],
    tier: str = "primary",
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """Return the assistant text for a chat-style message list."""
    model = _TIER_MODEL.get(tier, settings.llm_primary_model)
    common = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}

    try:
        resp = litellm.completion(**_local_kwargs(model), **common)
        return resp["choices"][0]["message"]["content"] or ""
    except Exception as exc:  # noqa: BLE001 - fall back on any local failure
        log.warning("Local LLM (%s) failed: %s. Trying Hugging Face fallback.", model, exc)
        fb = _fallback_kwargs()
        if fb is None:
            raise RuntimeError(
                f"Local LLM failed and no HF_TOKEN configured for fallback: {exc}"
            ) from exc
        resp = litellm.completion(**fb, **common)
        return resp["choices"][0]["message"]["content"] or ""


def complete(prompt: str, tier: str = "primary", **kwargs) -> str:
    """Convenience wrapper for a single user prompt."""
    return chat([{"role": "user", "content": prompt}], tier=tier, **kwargs)
