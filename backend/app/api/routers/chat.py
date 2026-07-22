"""Conversational assistant endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import Principal, require_permission
from app.models.assistant import Message
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag.chat_engine import answer

router = APIRouter(prefix="/chat", tags=["assistant"])


@router.post("/{customer_id}", response_model=ChatResponse)
def chat_with_customer(
    customer_id: uuid.UUID,
    body: ChatRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission("assistant.chat")),
) -> dict:
    user_id = uuid.UUID(principal.user_id) if principal.user_id else None
    return answer(db, customer_id, body.message, body.conversation_id, user_id)


@router.get("/{conversation_id}/messages")
def conversation_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_permission("assistant.chat")),
) -> list[dict]:
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()
    return [
        {"role": m.role, "content": m.content, "citations": m.citations, "created_at": m.created_at}
        for m in rows
    ]
