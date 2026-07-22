"""Chat request/response schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None


class Citation(BaseModel):
    source_type: str | None = None
    source_id: str | None = None
    snippet: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: list[Citation] = []
    intent: str | None = None
