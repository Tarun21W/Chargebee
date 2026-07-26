"""Admin endpoints — users / roles read + user create/delete."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.core.db import get_db
from app.core.security import Principal, get_principal, require_permission

router = APIRouter(prefix="/admin", tags=["admin"])


class NewUser(BaseModel):
    user_name: str
    email: str
    password: str = "Pulse@123"
    role: str = "CSM"


@router.post("/users", status_code=201)
def create_user(
    body: NewUser,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission("admin.manage")),
) -> dict:
    """Create a Supabase auth user + app User row and assign a role."""
    from app.models.admin import Role, User, UserRole

    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status_code=409, detail="A user with that email already exists.")

    uid = None
    if settings.supabase_url and settings.supabase_service_role_key:
        try:
            from supabase import create_client

            sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
            res = sb.auth.admin.create_user(
                {"email": body.email, "password": body.password, "email_confirm": True}
            )
            uid = res.user.id if res and res.user else None
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Auth user creation failed: {exc}") from exc

    u = User(user_name=body.user_name, email=body.email, supabase_uid=uid, is_active=True)
    db.add(u)
    db.flush()
    role = db.scalar(select(Role).where(Role.role_name == body.role))
    if role:
        db.add(UserRole(user_id=u.user_id, role_id=role.role_id))
    db.commit()
    write_audit(db, _principal_uid(principal), "user.create", "user", str(u.user_id))
    return {"user_id": str(u.user_id), "user_name": u.user_name, "email": u.email, "role": body.role}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_permission("admin.manage")),
) -> dict:
    """Delete an app user (+ its Supabase auth account), unlinking references first."""
    from app.models.admin import User

    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    if principal.user_id and str(user_id) == principal.user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    # Null out FK references so the delete isn't blocked (why deletes failed before).
    for tbl, col in [
        ("customers", "owner_user_id"),
        ("tickets", "assigned_user_id"),
        ("alerts", "acknowledged_by"),
        ("summaries", "generated_by"),
        ("conversations", "user_id"),
        ("audit_logs", "user_id"),
    ]:
        db.execute(text(f"UPDATE {tbl} SET {col} = NULL WHERE {col} = :id"), {"id": str(user_id)})

    uid = u.supabase_uid
    db.delete(u)  # user_roles cascade via FK
    db.commit()

    if uid and settings.supabase_url and settings.supabase_service_role_key:
        try:
            from supabase import create_client

            create_client(settings.supabase_url, settings.supabase_service_role_key).auth.admin.delete_user(uid)
        except Exception:  # noqa: BLE001 - app row already gone; auth cleanup best-effort
            pass

    write_audit(db, _principal_uid(principal), "user.delete", "user", str(user_id))
    return {"deleted": str(user_id)}


def _principal_uid(principal: Principal) -> uuid.UUID | None:
    return uuid.UUID(principal.user_id) if principal.user_id else None


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
