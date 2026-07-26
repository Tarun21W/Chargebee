"""LLM routing.

Primary: Ollama Cloud (hosted, high-quality model, e.g. gpt-oss:120b) via its
OpenAI-compatible endpoint, called directly with httpx. Fallback: a local Ollama
model (qwen2.5:7b) via LiteLLM, so the app keeps working offline or if the cloud
is unreachable. Embeddings stay local (bge-m3).
"""
from __future__ import annotations

import httpx
import litellm

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("app.llm")

litellm.drop_params = True


def _cloud_chat(messages: list[dict], temperature: float, max_tokens: int) -> str:
    resp = httpx.post(
        f"{settings.ollama_cloud_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.ollama_cloud_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.ollama_cloud_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=settings.llm_request_timeout,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"].get("content") or ""


def _local_chat(messages: list[dict], temperature: float, max_tokens: int) -> str:
    resp = litellm.completion(
        model=f"ollama/{settings.llm_fallback_model}",
        api_base=settings.ollama_base_url,
        timeout=settings.llm_request_timeout,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp["choices"][0]["message"]["content"] or ""


def chat(
    messages: list[dict],
    tier: str = "primary",
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> str:
    """Return assistant text. Ollama Cloud primary → local Ollama fallback."""
    if settings.ollama_cloud_api_key:
        try:
            return _cloud_chat(messages, temperature, max_tokens)
        except Exception as exc:  # noqa: BLE001 - fall back to local on any cloud failure
            log.warning(
                "Ollama Cloud (%s) failed: %s. Falling back to local %s.",
                settings.ollama_cloud_model, exc, settings.llm_fallback_model,
            )
    return _local_chat(messages, temperature, max_tokens)


def complete(prompt: str, tier: str = "primary", **kwargs) -> str:
    """Convenience wrapper for a single user prompt."""
    return chat([{"role": "user", "content": prompt}], tier=tier, **kwargs)
