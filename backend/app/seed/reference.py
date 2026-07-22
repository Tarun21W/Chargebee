"""Seed reference/config data shared across the platform."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.admin import Permission, Role, RolePermission, User, UserRole
from app.models.alerts import AlertRule, NotificationChannel
from app.models.assistant import AssistantConfig
from app.models.customer_data import DataSource, Product
from app.models.risk import ScoringModel
from app.models.summary import SummaryTemplate

# ---- Staff users (also become customer owners / ticket assignees) ----------
STAFF = [
    ("Ava Thompson", "ava@calispec.ai", "Admin"),
    ("Marco Reyes", "marco@calispec.ai", "CSM"),
    ("Priya Nair", "priya@calispec.ai", "CSM"),
    ("Liam Chen", "liam@calispec.ai", "Sales"),
    ("Sofia Rossi", "sofia@calispec.ai", "Support"),
]

ROLES = {
    "Admin": "Full access to all modules",
    "CSM": "Customer success manager",
    "Sales": "Sales representative",
    "Support": "Support agent",
}

# permission_name -> module
PERMISSIONS = {
    "customer.read": "CustomerData",
    "summary.generate": "Summarisation",
    "assistant.chat": "Assistant",
    "risk.read": "Risk",
    "alert.manage": "Alerts",
    "report.read": "Analytics",
    "admin.manage": "Administration",
}

ROLE_PERMS = {
    "Admin": list(PERMISSIONS.keys()),
    "CSM": ["customer.read", "summary.generate", "assistant.chat", "risk.read", "report.read"],
    "Sales": ["customer.read", "summary.generate", "assistant.chat", "risk.read"],
    "Support": ["customer.read", "summary.generate", "assistant.chat"],
}

PRODUCTS = [
    ("Analytics Suite", "Platform", 1200),
    ("API Access", "Platform", 400),
    ("Advanced Reporting", "Add-on", 300),
    ("Priority Support", "Service", 500),
    ("Data Connectors", "Add-on", 250),
    ("Mobile App", "Platform", 150),
]

SUMMARY_TEMPLATES = [
    (
        "CS Health Overview",
        "CustomerSuccess",
        "Summarise this customer's health, engagement and retention outlook for a CSM.",
    ),
    (
        "Support Context",
        "Support",
        "Summarise open issues, sentiment and support history for a support agent.",
    ),
    (
        "Sales Expansion",
        "Sales",
        "Summarise spend, plan and expansion/upsell opportunities for a sales rep.",
    ),
]

DATA_SOURCES = [
    ("Salesforce CRM", "CRM"),
    ("Stripe Billing", "Billing"),
    ("Zendesk", "Ticketing"),
    ("Product Analytics", "Usage"),
]

CHANNELS = [("Email", "email"), ("In-App", "in_app"), ("Slack", "slack")]

ALERT_RULES = [
    ("Churn risk high", "churn_score >= 70", "high"),
    ("Renewal within 30 days", "days_to_renewal <= 30", "medium"),
    ("Negative sentiment spike", "avg_ticket_sentiment <= -0.4", "high"),
    ("Payment past due", "subscription_status = 'past_due'", "high"),
]

SCORING_MODEL = (
    "Default Health & Churn v1",
    "weighted_sum(usage_trend, login_recency, ticket_load, sentiment, payment, renewal)",
    "100 - health",
    "1.0",
)

ASSISTANT = ("Customer Intelligence Assistant", "Concise, factual, cites sources", "single-customer", 10)


def seed_reference(db: Session) -> dict[str, User]:
    """Insert reference rows. Returns staff users keyed by name."""
    # Roles + permissions
    roles: dict[str, Role] = {}
    for name, desc in ROLES.items():
        r = Role(role_name=name, description=desc)
        db.add(r)
        roles[name] = r

    perms: dict[str, Permission] = {}
    for name, module in PERMISSIONS.items():
        p = Permission(permission_name=name, module=module)
        db.add(p)
        perms[name] = p
    db.flush()

    for role_name, perm_names in ROLE_PERMS.items():
        for pn in perm_names:
            db.add(RolePermission(role_id=roles[role_name].role_id, permission_id=perms[pn].permission_id))

    # Users + role assignment
    users: dict[str, User] = {}
    for name, email, role_name in STAFF:
        u = User(user_name=name, email=email, is_active=True)
        db.add(u)
        db.flush()
        db.add(UserRole(user_id=u.user_id, role_id=roles[role_name].role_id))
        users[name] = u

    # Products
    for pname, cat, price in PRODUCTS:
        db.add(Product(product_name=pname, category=cat, unit_price=price))

    # Templates / assistant / scoring model
    for tname, team, prompt in SUMMARY_TEMPLATES:
        db.add(SummaryTemplate(template_name=tname, team=team, prompt_text=prompt))
    aname, persona, scope, limit = ASSISTANT
    db.add(AssistantConfig(assistant_name=aname, persona=persona, scope=scope, context_limit=limit))
    mname, hf, cf, ver = SCORING_MODEL
    db.add(ScoringModel(model_name=mname, health_formula=hf, churn_formula=cf, version=ver))

    # Data sources / channels / alert rules
    for sname, stype in DATA_SOURCES:
        db.add(DataSource(source_name=sname, source_type=stype, connection_status="connected"))
    for cname, method in CHANNELS:
        db.add(NotificationChannel(channel_name=cname, delivery_method=method))
    for rname, cond, sev in ALERT_RULES:
        db.add(AlertRule(rule_name=rname, condition=cond, severity=sev, is_active=True))

    db.flush()
    return users
