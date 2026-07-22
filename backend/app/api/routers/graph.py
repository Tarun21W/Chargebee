"""Memory-graph query endpoints (Neo4j)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import Principal, require_permission
from app.services.graph import graph_enabled
from app.services.graph.queries import (
    customer_neighbourhood,
    customers_complaining_about,
    customers_using_feature,
)

router = APIRouter(prefix="/graph", tags=["graph"])


def _ensure_graph() -> None:
    if not graph_enabled():
        raise HTTPException(status_code=503, detail="Neo4j graph is not available.")


@router.get("/complaints")
def complaints(
    keyword: str = Query(..., description="topic/feature keyword"),
    _: Principal = Depends(require_permission("customer.read")),
) -> list[dict]:
    _ensure_graph()
    return customers_complaining_about(keyword)


@router.get("/feature")
def feature_users(
    name: str = Query(..., description="feature name"),
    _: Principal = Depends(require_permission("customer.read")),
) -> list[dict]:
    _ensure_graph()
    return customers_using_feature(name)


@router.get("/customers/{customer_id}/neighbourhood")
def neighbourhood(
    customer_id: str,
    _: Principal = Depends(require_permission("customer.read")),
) -> dict:
    _ensure_graph()
    return customer_neighbourhood(customer_id)
