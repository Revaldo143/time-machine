"""FalkorDB connection + schema helpers for TimeMachine.

The whole trick: every memory edge carries a validity interval
(valid_from / valid_to, ISO date strings). Old beliefs are closed,
never deleted — so any past belief state is reconstructible.
"""
import os

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

HOST = os.getenv("FALKORDB_HOST", "localhost")
PORT = int(os.getenv("FALKORDB_PORT", "6379"))
GRAPH_NAME = "timemachine"


def connect():
    """Return (db, graph) connected to the TimeMachine graph."""
    db = FalkorDB(host=HOST, port=PORT)
    return db, db.select_graph(GRAPH_NAME)


def reset(graph):
    """Wipe the graph so seeding is idempotent."""
    # Deleting all nodes also drops their relationships.
    graph.query("MATCH (n) DETACH DELETE n")


def as_of_filter(edge_alias: str, t: str) -> str:
    """Cypher fragment: edge was valid at time T (ISO date string)."""
    return (
        f"{edge_alias}.valid_from <= '{t}' AND "
        f"({edge_alias}.valid_to IS NULL OR {edge_alias}.valid_to > '{t}')"
    )
