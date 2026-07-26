"""SQLAlchemy models mirroring the Supabase schema (7 modules, 26 tables).

Importing this package registers every table on ``Base.metadata``.
"""
from app.models import (  # noqa: F401
    admin,
    alerts,
    assistant,
    customer_data,
    risk,
    summary,
)
