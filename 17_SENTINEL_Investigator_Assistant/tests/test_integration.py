"""Live checks against the real databases. Skipped unless RUN_INTEGRATION=1.

    $env:RUN_INTEGRATION = "1"; uv run pytest -m integration -v
"""
import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="set RUN_INTEGRATION=1 to run"),
]

KNOWN_TRANSACTION = "TX_0000082052"   # a validation-split transaction


@pytest.fixture(scope="module")
def live_service():
    from app.main import build_service
    service = build_service()
    yield service
    service.graph.close()


def test_supabase_transaction(live_service):
    tx = live_service.transactions.get_transaction(KNOWN_TRANSACTION)
    assert tx["transaction_id"] == KNOWN_TRANSACTION
    assert "fraud_label" not in tx
    assert live_service.transactions.get_transaction("TX_DOES_NOT_EXIST") is None


def test_neo4j_neighborhood_matches_transaction(live_service):
    tx = live_service.transactions.get_transaction(KNOWN_TRANSACTION)
    graph = live_service.graph.get_customer_neighborhood(tx["customer_id"], KNOWN_TRANSACTION)
    assert graph["transaction_found_in_graph"] is True
    assert graph["device_id"] == tx["device_id"] and graph["merchant_id"] == tx["merchant_id"]
    assert graph["cutoff_time"].startswith(tx["transaction_time"][:19])


def test_qdrant_top_five(live_service):
    hits = live_service.policies.search_policy("how to treat a shared device used by multiple customers")
    assert len(hits) == 5
    assert all(h["source_document"] and h["chunk_number"] is not None for h in hits)
    info = live_service.policies.store.collection_info()
    assert info["vector_size"] == 3072 and info["distance"] == "Cosine"
