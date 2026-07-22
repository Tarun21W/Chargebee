"""SQLAlchemy engine/session against the Supabase Postgres database."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# `future`/2.0 style engine. pool_pre_ping guards against dropped Supabase
# pooler connections.
engine = create_engine(
    settings.database_url or "postgresql+psycopg://localhost/postgres",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,  # recycle stale Supabase pooler connections
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
