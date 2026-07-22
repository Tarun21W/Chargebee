"""Audit-log helper for sensitive/AI-generating actions."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger

log = get_logger("app.audit")


def write_audit(
    db: Session,
    user_id: uuid.UUID | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
) -> None:
    from app.models.admin import AuditLog

    try:
        db.add(
            AuditLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id)
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 - auditing must never break the request
        log.warning("Audit write failed: %s", exc)
        db.rollback()
