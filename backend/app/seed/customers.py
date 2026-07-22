"""Generate realistic, internally-consistent synthetic customers.

Produces three archetypes so the risk, timeline and summary features have a
clear story to tell:
  - "at_risk": past-due/renewing soon, declining usage, negative tickets
  - "healthy": active, engaged, positive
  - "onboarding": new, ramping up
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import User
from app.models.customer_data import (
    DocChunk,
    Interaction,
    Order,
    OrderItem,
    Product,
    Subscription,
    Ticket,
    TicketMessage,
)

RNG = random.Random(42)  # deterministic seed for reproducible demos
TODAY = date(2026, 7, 17)
NOW = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)

COMPANIES = [
    "Northwind Traders", "Globex Corp", "Initech", "Umbrella Retail", "Soylent Foods",
    "Stark Industries", "Wayne Enterprises", "Acme Logistics", "Hooli", "Pied Piper",
    "Vandelay Imports", "Wonka Systems", "Cyberdyne", "Tyrell Corp", "Aperture Science",
    "Massive Dynamic", "Gekko Capital", "Oscorp", "Bluth Company", "Prestige Worldwide",
    "Dunder Mifflin", "Sterling Cooper", "Los Pollos", "Nakatomi Trading", "Wernham Hogg",
]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
SEG_PLAN = {"SMB": ("Starter", 300, 900), "Mid-Market": ("Pro", 1500, 4000), "Enterprise": ("Enterprise", 6000, 20000)}

ISSUE_TICKETS = [
    ("API returning intermittent 500 errors", "The API keeps failing on our checkout flow. This is impacting production and our customers are noticing."),
    ("Dashboard load times have gotten very slow", "Reports that used to load in seconds now take over a minute. The team is frustrated."),
    ("Data connector sync keeps failing", "Our Salesforce connector has failed three times this week. We're not getting fresh data."),
    ("Billing discrepancy on the latest invoice", "We were charged for seats we don't use. Please review invoice and issue a correction."),
    ("Cannot export reports to CSV", "The export button throws an error every time. We need this for our board meeting."),
    ("Feature adoption is lower than expected", "We're not seeing value from the Advanced Reporting add-on. Considering whether to keep it."),
]
POSITIVE_TICKETS = [
    ("Question about configuring SSO", "Just need a quick pointer on setting up SAML SSO for our team."),
    ("Request for a training session", "Could we schedule an onboarding walkthrough for three new hires?"),
    ("How do I set up custom alerts?", "Looking to configure alerting rules for our usage thresholds."),
]
AGENT_REPLIES = [
    "Thanks for flagging this — I've escalated to engineering and will update you within 24 hours.",
    "I understand the impact. We've applied a temporary mitigation and are investigating the root cause.",
    "Apologies for the trouble. I've issued a correction and confirmed it on your account.",
    "Happy to help — I've shared a guide and can hop on a call if useful.",
]


def _dt(days_ago: int, hour: int = 10) -> datetime:
    return NOW - timedelta(days=days_ago, hours=NOW.hour - hour)


def _archetype(i: int) -> str:
    if i < 5:
        return "at_risk"
    if i < 20:
        return "healthy"
    return "onboarding"


def seed_customers(db: Session) -> list[DocChunk]:
    products = list(db.scalars(select(Product)).all())
    staff = list(db.scalars(select(User)).all())
    owners = [u for u in staff]  # any staff can own
    from app.models.customer_data import Customer  # local import to avoid cycle

    doc_chunks: list[DocChunk] = []

    for i, company in enumerate(COMPANIES):
        arch = _archetype(i)
        segment = RNG.choice(list(SEG_PLAN))
        plan, mrr_lo, mrr_hi = SEG_PLAN[segment]
        mrr = RNG.randint(mrr_lo, mrr_hi)
        owner = RNG.choice(owners)
        signup_days = RNG.randint(60, 1000) if arch != "onboarding" else RNG.randint(10, 60)
        signup = TODAY - timedelta(days=signup_days)

        lifecycle = {"at_risk": "At-Risk", "healthy": "Active", "onboarding": "Onboarding"}[arch]

        customer = Customer(
            customer_name=company,
            account_id=f"ACC-{1000 + i}",
            email=f"contact@{company.split()[0].lower()}.com",
            phone=f"+1-555-{RNG.randint(1000, 9999)}",
            segment=segment,
            region=RNG.choice(REGIONS),
            lifecycle_stage=lifecycle,
            signup_date=signup,
            owner_user_id=owner.user_id,
        )
        db.add(customer)
        db.flush()

        # ---- Subscription -------------------------------------------------
        if arch == "at_risk":
            sub_status = RNG.choice(["past_due", "active"])
            renewal = TODAY + timedelta(days=RNG.randint(5, 30))  # renewal soon
        elif arch == "onboarding":
            sub_status, renewal = "active", TODAY + timedelta(days=RNG.randint(300, 360))
        else:
            sub_status, renewal = "active", TODAY + timedelta(days=RNG.randint(120, 300))
        db.add(
            Subscription(
                customer_id=customer.customer_id,
                plan=plan,
                mrr=mrr,
                start_date=signup,
                renewal_date=renewal,
                status=sub_status,
            )
        )

        # ---- Orders -------------------------------------------------------
        n_orders = RNG.randint(1, 5)
        for _ in range(n_orders):
            odate = signup + timedelta(days=RNG.randint(0, max(1, signup_days)))
            if odate > TODAY:
                odate = TODAY
            order = Order(customer_id=customer.customer_id, order_date=odate, total_amount=0, status="completed")
            db.add(order)
            db.flush()
            total = 0.0
            for prod in RNG.sample(products, RNG.randint(1, 3)):
                qty = RNG.randint(1, 4)
                db.add(OrderItem(order_id=order.order_id, product_id=prod.product_id, qty=qty, unit_price=float(prod.unit_price)))
                total += qty * float(prod.unit_price)
            order.total_amount = total

        # ---- Interactions (usage) ----------------------------------------
        # Healthy: steady recent logins. At-risk: usage tapers off recently.
        if arch == "healthy":
            login_days = sorted(RNG.sample(range(0, 60), 18))
        elif arch == "onboarding":
            login_days = sorted(RNG.sample(range(0, 45), 12))
        else:  # at_risk — most logins are older than 25 days
            login_days = sorted(RNG.sample(range(25, 90), 10) + RNG.sample(range(0, 25), 2))
        for d in login_days:
            db.add(Interaction(customer_id=customer.customer_id, type="login", channel="web", occurred_at=_dt(d)))
        for _ in range(RNG.randint(2, 6)):
            db.add(
                Interaction(
                    customer_id=customer.customer_id,
                    type="feature_use",
                    channel="app",
                    occurred_at=_dt(RNG.randint(0, 80)),
                    meta={"feature": RNG.choice(["Analytics Suite", "Advanced Reporting", "API Access"])},
                )
            )

        # ---- Tickets + messages + RAG docs -------------------------------
        if arch == "at_risk":
            n_tickets, pool, base_sent = RNG.randint(3, 6), ISSUE_TICKETS, -0.6
        elif arch == "healthy":
            n_tickets, pool, base_sent = RNG.randint(0, 2), POSITIVE_TICKETS, 0.4
        else:
            n_tickets, pool, base_sent = RNG.randint(1, 3), POSITIVE_TICKETS + ISSUE_TICKETS[:2], 0.1

        for _ in range(n_tickets):
            subject, body = RNG.choice(pool)
            opened_days = RNG.randint(1, 45)
            is_open = arch == "at_risk" and RNG.random() < 0.5
            sentiment = round(max(-1.0, min(1.0, base_sent + RNG.uniform(-0.2, 0.2))), 3)
            priority = RNG.choice(["high", "urgent"]) if base_sent < 0 else RNG.choice(["low", "medium"])
            ticket = Ticket(
                customer_id=customer.customer_id,
                subject=subject,
                status="open" if is_open else "closed",
                priority=priority,
                sentiment=sentiment,
                opened_at=_dt(opened_days),
                closed_at=None if is_open else _dt(max(0, opened_days - RNG.randint(1, 5))),
                assigned_user_id=owner.user_id,
            )
            db.add(ticket)
            db.flush()

            transcript = [f"[{subject}]"]
            db.add(TicketMessage(ticket_id=ticket.ticket_id, sender="customer", body=body, sentiment=sentiment, created_at=_dt(opened_days)))
            transcript.append(f"Customer: {body}")
            reply = RNG.choice(AGENT_REPLIES)
            db.add(TicketMessage(ticket_id=ticket.ticket_id, sender="agent", body=reply, sentiment=0.2, created_at=_dt(max(0, opened_days - 1))))
            transcript.append(f"Agent: {reply}")

            doc_chunks.append(
                DocChunk(
                    customer_id=customer.customer_id,
                    source_type="ticket",
                    source_id=str(ticket.ticket_id),
                    chunk_text="\n".join(transcript),
                )
            )

        # ---- Account note (RAG doc) --------------------------------------
        note = _account_note(company, arch, segment, plan, mrr, sub_status, renewal)
        doc_chunks.append(
            DocChunk(customer_id=customer.customer_id, source_type="note", source_id=None, chunk_text=note)
        )

    db.add_all(doc_chunks)
    db.flush()
    return doc_chunks


def _account_note(company, arch, segment, plan, mrr, sub_status, renewal) -> str:
    if arch == "at_risk":
        extra = (
            f" The account has raised repeated product issues and a stakeholder mentioned they are "
            f"evaluating a competitor. Usage has declined over the last month. Subscription status is "
            f"'{sub_status}' with renewal on {renewal.isoformat()} — retention is a concern."
        )
    elif arch == "onboarding":
        extra = " The customer is new and still ramping up; focus is on activation and training."
    else:
        extra = " The customer is engaged and healthy with steady usage and positive sentiment."
    return (
        f"Account note for {company}. Segment: {segment}. Plan: {plan} at ${mrr}/mo (MRR)."
        + extra
    )
