"""Admin endpoints (users/roles read). Expanded in Phase 11/12."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import Principal, get_principal

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me")
def whoami(principal: Principal = Depends(get_principal)) -> dict:
    return {
        "supabase_uid": principal.supabase_uid,
        "email": principal.email,
        "user_id": principal.user_id,
        "roles": principal.roles,
        "permissions": sorted(principal.permissions),
        "is_dev": principal.is_dev,
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: Principal = Depends(get_principal),
) -> list[dict]:
    from app.models.admin import User

    rows = db.scalars(select(User).limit(200)).all()
    return [
        {"user_id": str(u.user_id), "user_name": u.user_name, "email": u.email, "is_active": u.is_active}
        for u in rows
    ]


@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    _: Principal = Depends(get_principal),
) -> list[dict]:
    from app.models.admin import Permission, Role, RolePermission

    roles = db.scalars(select(Role)).all()
    out = []
    for r in roles:
        perm_ids = db.scalars(
            select(RolePermission.permission_id).where(RolePermission.role_id == r.role_id)
        ).all()
        perms = (
            db.scalars(select(Permission.permission_name).where(Permission.permission_id.in_(perm_ids))).all()
            if perm_ids
            else []
        )
        out.append(
            {"role_id": str(r.role_id), "role_name": r.role_name, "description": r.description, "permissions": sorted(perms)}
        )
    return out
