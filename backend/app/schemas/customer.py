"""Pydantic response schemas for customer data."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerBrief(ORMModel):
    customer_id: uuid.UUID
    customer_name: str
    segment: str | None = None
    region: str | None = None
    lifecycle_stage: str | None = None


class TicketOut(ORMModel):
    ticket_id: uuid.UUID
    subject: str
    status: str
    priority: str
    sentiment: float | None = None
    opened_at: datetime
    closed_at: datetime | None = None


class OrderOut(ORMModel):
    order_id: uuid.UUID
    order_date: date
    total_amount: float
    status: str


class SubscriptionOut(ORMModel):
    subscription_id: uuid.UUID
    plan: str
    mrr: float
    start_date: date | None = None
    renewal_date: date | None = None
    status: str


class InteractionOut(ORMModel):
    interaction_id: uuid.UUID
    type: str
    channel: str | None = None
    occurred_at: datetime


class CustomerDetail(CustomerBrief):
    account_id: str | None = None
    email: str | None = None
    phone: str | None = None
    signup_date: date | None = None
    tickets: list[TicketOut] = []
    orders: list[OrderOut] = []
    subscriptions: list[SubscriptionOut] = []
    interactions: list[InteractionOut] = []
