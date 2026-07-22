"""Summary request/response schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SummaryRequest(BaseModel):
    team: str = "CustomerSuccess"


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    section_name: str
    display_order: int
    content: str | None = None
    citations: list | None = None


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    summary_id: uuid.UUID
    summary_type: str
    confidence_level: float | None = None
    generated_date: datetime
    sections: list[SectionOut] = []
