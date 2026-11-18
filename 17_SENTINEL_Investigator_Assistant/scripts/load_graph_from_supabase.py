"""
One-off: load the Supabase SENTINEL dataset into the investigator's Neo4j graph.

Why this exists
    The graph in NEO4J_Graph_CustMerchDevice was loaded from a different (larger)
    generation of the SENTINEL data: none of its PAID.transaction_id values exist in
    Supabase, and shared customer IDs belong to different people. To attach correct
    graph evidence to a Supabase transaction, we load the Supabase kit's data into a
    separate Neo4j instance (bolt://localhost:7688) with the SAME graph model.

What is reused
    All reading, node/edge building and MERGE statements come from the existing
    NEO4J_Graph_CustMerchDevice/graph_loader.py. We only point it at the data folder
    of supabase_db_kit (the files Supabase was loaded from) and load every split
    instead of a 14-day window.

What is added
    PAID.label_available_at and PAID.split, so the investigator can refuse to use
    labels that were not yet known at the time of the transaction being investigated.

Safe to run twice (MERGE). Afterwards it verifies every PAID edge against Supabase.

    uv run python scripts/load_graph_from_supabase.py
"""
import sys
from pathlib import Path

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"C:\tmp\sentinel\NEO4J_Graph_CustMerchDevice")

import graph_loader  # noqa: E402  (the existing project's loader)

from app.config import get_settings  # noqa: E402

SUPABASE_DATA_DIR = r"C:\tmp\sentinel\supabase_db_kit\data\tables"
SPLITS = ["warmup", "train", "validation", "holdout"]

# Range indexes so the time-window queries in app/db/neo4j_db.py stay fast.
EXTRA_INDEXES = [
    "CREATE INDEX paid_time IF NOT EXISTS FOR ()-[p:PAID]-() ON (p.time)",
    "CREATE INDEX paid_device IF NOT EXISTS FOR ()-[p:PAID]-() ON (p.device_id)",
]

SET_LABEL_TIMING = """
UNWIND $rows AS row
MATCH ()-[p:PAID {transaction_id: row.transaction_id}]->()
SET p.label_available_at = datetime(row.label_available_at),
    p.split = row.split
"""


def read_all_payments() -> pd.DataFrame:
    """All transactions with their label, using the existing read_table helper."""
    frames = []
    for split in SPLITS:
        tx = graph_loader.read_table("transactions", split, [
            "transaction_id", "customer_id", "merchant_id", "device_id",
            "transaction_amount", "payment_channel", "transaction_time", "split",
        ])
        labels = graph_loader.read_table("labels", split, [
            "transaction_id", "fraud_label", "label_available_at",
        ])
        frames.append(tx.merge(labels, on="transaction_id", how="left"))
    tx = pd.concat(frames, ignore_index=True)
    tx["transaction_time"] = pd.to_datetime(tx["transaction_time"], utc=True)
    tx["fraud_label"] = tx["fraud_label"].fillna(0).astype(int)
    return tx.sort_values("transaction_time").reset_index(drop=True)


def verify_against_supabase(driver, db_url: str) -> None:
    """Every PAID edge must match the Supabase row with the same transaction_id."""
    records, _, _ = driver.execute_query("""
        MATCH (c:Customer)-[p:PAID]->(m:Merchant)
        RETURN p.transaction_id AS tx, c.customer_id AS customer_id,
               m.merchant_id AS merchant_id, p.device_id AS device_id
    """)
    graph = {r["tx"]: (r["customer_id"], r["merchant_id"], r["device_id"]) for r in records}
    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute("SELECT transaction_id, customer_id, merchant_id, device_id FROM public.transactions")
        supabase = {row[0]: tuple(row[1:]) for row in cur.fetchall()}
    missing = set(supabase) - set(graph)
    extra = set(graph) - set(supabase)
    mismatched = [tx for tx in set(graph) & set(supabase) if graph[tx] != supabase[tx]]
    print(f"Verification: supabase={len(supabase):,} graph={len(graph):,} "
          f"missing={len(missing)} extra={len(extra)} mismatched={len(mismatched)}")
    if missing or extra or mismatched:
        raise SystemExit("Graph does not match Supabase")


def main() -> None:
    settings = get_settings()
    graph_loader.DATA_DIR = SUPABASE_DATA_DIR

    tx = read_all_payments()
    print(f"Payments: {len(tx):,} ({tx['fraud_label'].sum()} fraud), "
          f"{tx['transaction_time'].min()} -> {tx['transaction_time'].max()}")
    rows = graph_loader.build_rows(tx)

    timing_rows = graph_loader.to_records(tx[["transaction_id", "label_available_at", "split"]])

    with graph_loader.connect(settings.neo4j_uri, settings.neo4j_user,
                              settings.neo4j_password.get_secret_value()) as driver:
        graph_loader.create_constraints(driver)
        for statement in EXTRA_INDEXES:
            driver.execute_query(statement)
        graph_loader.load_graph(driver, rows)
        graph_loader.write_in_batches(driver, SET_LABEL_TIMING, timing_rows)
        print("Graph now has:", graph_loader.graph_counts(driver))
        verify_against_supabase(driver, settings.supabase_db_url.get_secret_value())


if __name__ == "__main__":
    main()
