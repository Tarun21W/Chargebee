"""Module 2 — Customer Summarisation."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class SummaryTemplate(Base):
    __tablename__ = "summary_templates"

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String)  # Support / Sales / CustomerSuccess
    prompt_text: Mapped[str] = mapped_column(Text)


class Summary(Base):
    __tablename__ = "summaries"

    summary_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("summary_templates.template_id"))
    summary_type: Mapped[str] = mapped_column(String, default="general")
    generated_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confidence_level: Mapped[float | None] = mapped_column(Numeric(4, 3))
    body: Mapped[str | None] = mapped_column(Text)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.user_id"))

    sections: Mapped[list["SummarySection"]] = relationship(
        back_populates="summary", order_by="SummarySection.display_order"
    )


class SummarySection(Base):
    __tablename__ = "summary_sections"

    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("summaries.summary_id"))
    section_name: Mapped[str] = mapped_column(String)  # Activity / Issues / Insights / Recommendations
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str | None] = mapped_column(Text)
    citations: Mapped[list | None] = mapped_column(JSONB)

    summary: Mapped["Summary"] = relationship(back_populates="sections")
