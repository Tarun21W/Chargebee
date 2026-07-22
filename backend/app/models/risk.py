"""Module 4 — Risk & Health Scoring."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ScoringModel(Base):
    __tablename__ = "scoring_models"

    model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    health_formula: Mapped[str | None] = mapped_column(Text)
    churn_formula: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String, default="1.0")


class Score(Base):
    __tablename__ = "scores"

    score_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    model_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scoring_models.model_id"))
    score_type: Mapped[str] = mapped_column(String)  # health / churn
    value: Mapped[float] = mapped_column(Numeric(6, 2))
    risk_level: Mapped[str | None] = mapped_column(String)  # Low / Medium / High
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    factors: Mapped[list["RiskFactor"]] = relationship(back_populates="score")


class RiskFactor(Base):
    """Per-feature contribution — powers SHAP-style explainability."""

    __tablename__ = "risk_factors"

    factor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    score_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scores.score_id"))
    factor_name: Mapped[str] = mapped_column(String)
    weight: Mapped[float] = mapped_column(Numeric(6, 4))
    contribution: Mapped[float] = mapped_column(Numeric(6, 4))  # signed points toward the score

    score: Mapped["Score"] = relationship(back_populates="factors")
