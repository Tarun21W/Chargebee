"""Module 6 — Analytics & Reporting."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ReportTemplate(Base):
    __tablename__ = "report_templates"

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name: Mapped[str] = mapped_column(String, nullable=False)
    report_type: Mapped[str] = mapped_column(String)
    layout: Mapped[dict | None] = mapped_column(JSONB)


class Report(Base):
    __tablename__ = "reports"

    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("report_templates.template_id"))
    report_name: Mapped[str] = mapped_column(String)
    generated_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    generated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.user_id"))
    parameters: Mapped[dict | None] = mapped_column(JSONB)
