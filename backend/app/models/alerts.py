"""Module 5 — Alerts & Notifications."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name: Mapped[str] = mapped_column(String, nullable=False)
    condition: Mapped[str] = mapped_column(Text)  # human/JSON rule expression
    severity: Mapped[str] = mapped_column(String, default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("alert_rules.rule_id"))
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    alert_type: Mapped[str] = mapped_column(String)
    alert_status: Mapped[str] = mapped_column(String, default="open")
    severity: Mapped[str] = mapped_column(String, default="medium")
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.user_id"))


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    channel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    delivery_method: Mapped[str] = mapped_column(String)  # email / in_app / slack


class AlertNotification(Base):
    __tablename__ = "alert_notifications"

    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alerts.alert_id"), primary_key=True)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notification_channels.channel_id"), primary_key=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_status: Mapped[str] = mapped_column(String, default="pending")
