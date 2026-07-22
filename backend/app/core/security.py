"""Supabase JWT verification + RBAC dependencies for FastAPI.

Supabase issues HS256-signed JWTs using the project's JWT secret. We verify the
signature locally (no network round-trip) and map the token's `sub` (Supabase
user id) to an application `User` row to resolve roles/permissions.

In development, if SUPABASE_JWT_SECRET is unset the guard falls back to an
anonymous dev principal so the API can be exercised without auth wiring.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db

_bearer = HTTPBearer(auto_error=False)


from app.core.cache import TTLCache

# Resolved identity (user_id, roles, permissions) keyed by Supabase uid. Avoids
# 4+ DB round-trips on every authenticated request — the dominant API latency.
_principal_cache = TTLCache(ttl=120)


@lru_cache
def _jwks_client() -> PyJWKClient:
    """Client for Supabase's public signing keys (asymmetric JWTs).

    Caches the fetched JWK set for an hour so token verification is local (no
    network round-trip per request)."""
    url = settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    return PyJWKClient(url, cache_jwk_set=True, lifespan=3600)


@dataclass
class Principal:
    """The authenticated caller, resolved from the JWT + app User row."""

    supabase_uid: str | None
    email: str | None
    user_id: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)
    is_dev: bool = False

    def has_permission(self, name: str) -> bool:
        return self.is_dev or name in self.permissions


def _decode(token: str) -> dict:
    """Verify a Supabase access token.

    Newer Supabase projects sign with an asymmetric key (ES256/RS256) exposed via
    JWKS; legacy projects use an HS256 shared secret. We pick the path based on the
    token's own `alg` header so both work.
    """
    try:
        alg = jwt.get_unverified_header(token).get("alg", "")
        if alg == "HS256":
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        # Asymmetric: verify against Supabase's published public key.
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[alg],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:  # pragma: no cover - passthrough to 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc


def get_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Principal:
    # Dev fallback: no secret configured -> allow anonymous full-access principal.
    if not settings.supabase_jwt_secret:
        return Principal(supabase_uid=None, email="dev@local", is_dev=True)

    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )

    claims = _decode(creds.credentials)
    uid = claims.get("sub")
    email = claims.get("email")

    principal = Principal(supabase_uid=uid, email=email)

    # Fast path: reuse the cached identity resolution for this uid.
    cached = _principal_cache.get(uid) if uid else None
    if cached is not None:
        principal.user_id = cached["user_id"]
        principal.roles = list(cached["roles"])
        principal.permissions = set(cached["permissions"])
        return principal

    # Lazy import to avoid a circular import at module load time.
    from app.models.admin import Permission, Role, RolePermission, User, UserRole

    user = db.scalar(select(User).where(User.supabase_uid == uid))
    if user is None:
        # Authenticated in Supabase but not provisioned in the app yet.
        return principal

    principal.user_id = str(user.user_id)
    role_ids = db.scalars(
        select(UserRole.role_id).where(UserRole.user_id == user.user_id)
    ).all()
    if role_ids:
        principal.roles = list(
            db.scalars(select(Role.role_name).where(Role.role_id.in_(role_ids))).all()
        )
        perm_ids = db.scalars(
            select(RolePermission.permission_id).where(
                RolePermission.role_id.in_(role_ids)
            )
        ).all()
        if perm_ids:
            principal.permissions = set(
                db.scalars(
                    select(Permission.permission_name).where(
                        Permission.permission_id.in_(perm_ids)
                    )
                ).all()
            )
    if uid:
        _principal_cache.set(
            uid,
            {"user_id": principal.user_id, "roles": principal.roles, "permissions": list(principal.permissions)},
        )
    return principal


def require_permission(name: str):
    """Dependency factory enforcing a named permission."""

    def _guard(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_permission(name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {name}",
            )
        return principal

    return _guard
