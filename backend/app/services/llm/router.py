"""LLM routing via LiteLLM.

Primary: a large Hugging Face Inference model (e.g. Qwen2.5-72B-Instruct) for
best quality. Fallback: the local Ollama model, so the API keeps working when
HF is unavailable, rate-limited, or times out (and for fully-offline use).

Task tiers only affect the local fallback model choice:
  - "fast"/"primary" -> local primary model
  - "heavy"          -> local heavy model
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


def _hf_kwargs() -> dict | None:
    if not settings.hf_token or not settings.hf_primary_model:
        return None
    return {
        "model": f"huggingface/{settings.hf_primary_model}",
        "api_key": settings.hf_token,
        "timeout": settings.llm_request_timeout,
    }


def _local_kwargs(model: str) -> dict:
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
    """Return the assistant text. HF primary → local Ollama fallback."""
    common = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}

    # Primary: Hugging Face large model.
    hf = _hf_kwargs()
    if hf is not None:
        try:
            resp = litellm.completion(**hf, **common)
            return resp["choices"][0]["message"]["content"] or ""
        except Exception as exc:  # noqa: BLE001 - fall back to local on any HF failure
            log.warning(
                "HF primary (%s) failed: %s. Falling back to local Ollama.",
                settings.hf_primary_model, exc,
            )

    # Fallback: local Ollama.
    model = _TIER_MODEL.get(tier, settings.llm_primary_model)
    try:
        resp = litellm.completion(**_local_kwargs(model), **common)
        return resp["choices"][0]["message"]["content"] or ""
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Both HF primary and local Ollama ({model}) failed: {exc}"
        ) from exc


def complete(prompt: str, tier: str = "primary", **kwargs) -> str:
    """Convenience wrapper for a single user prompt."""
    return chat([{"role": "user", "content": prompt}], tier=tier, **kwargs)
