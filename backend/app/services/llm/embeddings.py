"""BGE-M3 embeddings via Ollama (through LiteLLM).

Centralised so seeding, ingestion and RAG all produce identical vectors.
"""
from __future__ import annotations

import litellm

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("app.embeddings")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input."""
    if not texts:
        return []
    resp = litellm.embedding(
        model=f"ollama/{settings.embed_model}",
        input=texts,
        api_base=settings.ollama_base_url,
        timeout=settings.llm_request_timeout,
    )
    # LiteLLM normalises to an OpenAI-style response; preserve input order.
    items = sorted(resp["data"], key=lambda d: d.get("index", 0))
    return [item["embedding"] for item in items]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
