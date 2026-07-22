"""Sync the relational customer data into the Neo4j memory graph.

Nodes:  Customer, Product, Feature, Topic, Subscription, User
Edges:  BOUGHT, USES_FEATURE, COMPLAINED_ABOUT, SUBSCRIBES_TO, OWNED_BY
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.admin import User
from app.models.customer_data import Customer, Interaction, Order, Subscription, Ticket

log = get_logger("app.graph.sync")

_RESET = "MATCH (n) DETACH DELETE n"

_CONSTRAINTS = [
    "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT feature_name IF NOT EXISTS FOR (f:Feature) REQUIRE f.name IS UNIQUE",
    "CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
]


def sync_all(db: Session) -> dict:
    from app.services.graph import get_driver

    driver = get_driver()
    counts = {"customers": 0, "edges": 0}

    with driver.session() as sess:
        sess.run(_RESET)
        for c in _CONSTRAINTS:
            sess.run(c)

        users = {str(u.user_id): u.user_name for u in db.scalars(select(User)).all()}

        customers = db.scalars(
            select(Customer).options(
                selectinload(Customer.orders).selectinload(Order.items),
                selectinload(Customer.tickets),
                selectinload(Customer.interactions),
                selectinload(Customer.subscriptions),
            )
        ).all()

        for c in customers:
            counts["customers"] += 1
            sess.run(
                """
                MERGE (c:Customer {id:$id})
                SET c.name=$name, c.segment=$segment, c.lifecycle=$lifecycle, c.region=$region
                """,
                id=str(c.customer_id),
                name=c.customer_name,
                segment=c.segment,
                lifecycle=c.lifecycle_stage,
                region=c.region,
            )

            if c.owner_user_id and str(c.owner_user_id) in users:
                sess.run(
                    """
                    MERGE (u:User {id:$uid}) SET u.name=$uname
                    WITH u MATCH (c:Customer {id:$cid})
                    MERGE (c)-[:OWNED_BY]->(u)
                    """,
                    uid=str(c.owner_user_id),
                    uname=users[str(c.owner_user_id)],
                    cid=str(c.customer_id),
                )
                counts["edges"] += 1

            # BOUGHT products
            product_names = {i.product.product_name for o in c.orders for i in o.items if i.product}
            for pname in product_names:
                sess.run(
                    """
                    MERGE (p:Product {name:$pname})
                    WITH p MATCH (c:Customer {id:$cid})
                    MERGE (c)-[:BOUGHT]->(p)
                    """,
                    pname=pname,
                    cid=str(c.customer_id),
                )
                counts["edges"] += 1

            # USES_FEATURE from interaction metadata
            features = {
                (i.meta or {}).get("feature")
                for i in c.interactions
                if i.type == "feature_use" and i.meta
            }
            for feat in filter(None, features):
                sess.run(
                    """
                    MERGE (f:Feature {name:$feat})
                    WITH f MATCH (c:Customer {id:$cid})
                    MERGE (c)-[:USES_FEATURE]->(f)
                    """,
                    feat=feat,
                    cid=str(c.customer_id),
                )
                counts["edges"] += 1

            # COMPLAINED_ABOUT topics (from negative-sentiment tickets)
            for t in c.tickets:
                if t.sentiment is not None and float(t.sentiment) < -0.2:
                    sess.run(
                        """
                        MERGE (topic:Topic {name:$name})
                        WITH topic MATCH (c:Customer {id:$cid})
                        MERGE (c)-[r:COMPLAINED_ABOUT]->(topic)
                        SET r.sentiment=$sent
                        """,
                        name=t.subject,
                        cid=str(c.customer_id),
                        sent=float(t.sentiment),
                    )
                    counts["edges"] += 1

            # SUBSCRIBES_TO plan
            for s in c.subscriptions:
                sess.run(
                    """
                    MERGE (pl:Plan {name:$plan})
                    WITH pl MATCH (c:Customer {id:$cid})
                    MERGE (c)-[r:SUBSCRIBES_TO]->(pl)
                    SET r.mrr=$mrr, r.status=$status, r.renewal=$renewal
                    """,
                    plan=s.plan,
                    cid=str(c.customer_id),
                    mrr=float(s.mrr),
                    status=s.status,
                    renewal=s.renewal_date.isoformat() if s.renewal_date else None,
                )
                counts["edges"] += 1

    log.info("Graph sync: %s", counts)
    return counts
