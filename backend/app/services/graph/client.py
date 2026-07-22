"""Neo4j driver management (lazy singleton)."""
from __future__ import annotations

from neo4j import Driver, GraphDatabase

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("app.graph")

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


def graph_enabled() -> bool:
    """True if Neo4j is reachable."""
    try:
        get_driver().verify_connectivity()
        return True
    except Exception as exc:  # noqa: BLE001
        log.debug("Neo4j not reachable: %s", exc)
        return False
