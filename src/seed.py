"""Seed the demo dataset: 'The Checkout Outage' — a 2-week incident timeline.

The agent's belief about the root cause changes 4 times as new evidence
arrives. Each superseded belief edge is CLOSED with valid_to (never deleted),
which is exactly what makes time-travel queries possible.
"""
from .graph import connect, reset

TOPIC = "checkout-outage"

# (date, evidence_text, source, new_belief)
TIMELINE = [
    (
        "2026-10-04",
        "Cache hit rate dropped from 95% to 40% on checkout-api",
        "datadog: cache dashboard",
        "Cache misconfiguration caused the checkout outage",
    ),
    (
        "2026-10-07",
        "DB connection pool exhausted — 500 waiting threads on orders-db",
        "pagerduty: incident #4821",
        "Connection pool exhaustion caused the checkout outage",
    ),
    (
        "2026-10-10",
        "Deploy v2.4 halved the pool size from 100 to 50",
        "github: PR #2214 review",
        "Bad deploy v2.4 caused the checkout outage",
    ),
    (
        "2026-10-14",
        "Traffic spiked 3x during the Diwali sale; pool size was fine for normal load",
        "cloudwatch: traffic report",
        "Traffic spike overwhelmed the pool; the deploy was a red herring",
    ),
]


def seed(graph_name="timemachine", skip=()):
    """Seed the timeline. `skip` = evidence ids to leave out (for what-if forks).

    Skipping an evidence also drops the claim it alone supported, and the
    valid_to chain is recomputed — so the fork is a genuine alternate history.
    """
    db, _ = connect()
    g = db.select_graph(graph_name)
    reset(g)

    g.query(
        "CREATE (:Agent {name: 'oncall-agent'})-[:MONITORS]->(:Topic {name: $topic})",
        {"topic": TOPIC},
    )

    prev_belief_id = None
    for i, (date, evidence, source, belief) in enumerate(TIMELINE):
        claim_id = f"claim-{i}"
        ev_id = f"evidence-{i}"
        if ev_id in skip:
            continue
        # Claim + evidence nodes, linked to the topic
        g.query(
            """
            MATCH (t:Topic {name: $topic})
            CREATE (c:Claim {id: $cid, text: $belief})-[:ABOUT]->(t),
                   (e:Evidence {id: $eid, text: $ev, source: $src, observed_at: $date})<-[:SUPPORTED_BY {valid_from: $date}]-(c)
            """,
            {"topic": TOPIC, "cid": claim_id, "belief": belief,
             "eid": ev_id, "ev": evidence, "src": source, "date": date},
        )
        # Close the previous belief (it was valid until today), open the new one
        if prev_belief_id is not None:
            g.query(
                """
                MATCH (:Agent {name: 'oncall-agent'})-[b:BELIEVES]->(:Claim {id: $cid})
                SET b.valid_to = $date
                """,
                {"cid": prev_belief_id, "date": date},
            )
        g.query(
            """
            MATCH (a:Agent {name: 'oncall-agent'}), (c:Claim {id: $cid})
            CREATE (a)-[:BELIEVES {valid_from: $date}]->(c)
            """,
            {"cid": claim_id, "date": date},
        )
        prev_belief_id = claim_id
        print(f"  [{date}] belief -> {belief[:60]}...")

    n = g.query("MATCH (n) RETURN count(n) AS c").result_set[0][0]
    skipped = f" (skipped: {sorted(skip)})" if skip else ""
    print(f"\nSeeded {n} nodes into graph '{graph_name}'.{skipped}")


if __name__ == "__main__":
    print("Seeding 'The Checkout Outage' timeline...")
    seed()
