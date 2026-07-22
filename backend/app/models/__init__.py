"""SQLAlchemy models mirroring the Supabase schema (7 modules, ~34 tables).

Importing this package registers every table on ``Base.metadata``.
"""
from app.models import (  # noqa: F401
    admin,
    alerts,
    analytics,
    assistant,
    customer_data,
    risk,
    summary,
)
