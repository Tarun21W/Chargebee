"""Module 1 — Customer Data Retrieval / Integration."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.db import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    account_id: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    segment: Mapped[str | None] = mapped_column(String)          # SMB / Mid-Market / Enterprise
    region: Mapped[str | None] = mapped_column(String)
    lifecycle_stage: Mapped[str | None] = mapped_column(String)  # Onboarding / Active / At-Risk / Churned
    signup_date: Mapped[date | None] = mapped_column(Date)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.user_id"))

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="customer")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    interactions: Mapped[list["Interaction"]] = relationship(back_populates="customer")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="customer")


class DataSource(Base):
    __tablename__ = "data_sources"

    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # CRM / Billing / Ticketing / Usage
    connection_status: Mapped[str] = mapped_column(String, default="disconnected")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FieldMapping(Base):
    __tablename__ = "field_mappings"

    mapping_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_field: Mapped[str] = mapped_column(String, nullable=False)
    unified_field: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.source_id"))


class SyncLog(Base):
    __tablename__ = "sync_logs"

    sync_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.source_id"))
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.customer_id"))
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="success")
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Interaction(Base):
    __tablename__ = "interactions"

    interaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    type: Mapped[str] = mapped_column(String)     # login / feature_use / email / call / meeting
    channel: Mapped[str | None] = mapped_column(String)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB)

    customer: Mapped["Customer"] = relationship(back_populates="interactions")


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    subject: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")     # open / pending / closed
    priority: Mapped[str] = mapped_column(String, default="medium") # low / medium / high / urgent
    sentiment: Mapped[float | None] = mapped_column(Numeric(4, 3))  # -1..1
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.user_id"))

    customer: Mapped["Customer"] = relationship(back_populates="tickets")
    messages: Mapped[list["TicketMessage"]] = relationship(back_populates="ticket")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.ticket_id"))
    sender: Mapped[str] = mapped_column(String)   # customer / agent
    body: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    ticket: Mapped["Ticket"] = relationship(back_populates="messages")


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    order_date: Mapped[date] = mapped_column(Date)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String, default="completed")

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.order_id"), primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    plan: Mapped[str] = mapped_column(String)      # Starter / Pro / Enterprise
    mrr: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    start_date: Mapped[date | None] = mapped_column(Date)
    renewal_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="active")  # active / past_due / cancelled

    customer: Mapped["Customer"] = relationship(back_populates="subscriptions")


class DocChunk(Base):
    """Text chunks (ticket transcripts, notes, docs) embedded for RAG."""

    __tablename__ = "doc_chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.customer_id"))
    source_type: Mapped[str] = mapped_column(String)  # ticket / note / doc / interaction
    source_id: Mapped[str | None] = mapped_column(String)
    chunk_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embed_dim))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
