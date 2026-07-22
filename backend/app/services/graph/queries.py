"""Read queries over the Neo4j memory graph."""
from __future__ import annotations

from app.services.graph import get_driver


def customers_complaining_about(keyword: str, limit: int = 25) -> list[dict]:
    """Find customers who complained about a topic matching `keyword`."""
    cypher = """
    MATCH (c:Customer)-[r:COMPLAINED_ABOUT]->(t:Topic)
    WHERE toLower(t.name) CONTAINS toLower($kw)
    RETURN c.name AS customer, c.id AS customer_id, t.name AS topic, r.sentiment AS sentiment
    ORDER BY r.sentiment ASC
    LIMIT $limit
    """
    with get_driver().session() as sess:
        return [dict(rec) for rec in sess.run(cypher, kw=keyword, limit=limit)]


def customers_using_feature(feature: str, limit: int = 25) -> list[dict]:
    cypher = """
    MATCH (c:Customer)-[:USES_FEATURE]->(f:Feature)
    WHERE toLower(f.name) CONTAINS toLower($feat)
    RETURN c.name AS customer, c.id AS customer_id, f.name AS feature
    LIMIT $limit
    """
    with get_driver().session() as sess:
        return [dict(rec) for rec in sess.run(cypher, feat=feature, limit=limit)]


def customer_neighbourhood(customer_id: str) -> dict:
    """Everything one hop from a customer — products, features, complaints, owner."""
    cypher = """
    MATCH (c:Customer {id:$cid})-[r]->(n)
    RETURN type(r) AS rel, labels(n)[0] AS kind, coalesce(n.name, n.id) AS name
    """
    with get_driver().session() as sess:
        rows = [dict(rec) for rec in sess.run(cypher, cid=customer_id)]
    return {"customer_id": customer_id, "relationships": rows}
