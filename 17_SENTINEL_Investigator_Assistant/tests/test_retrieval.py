"""Retrieval layer: Supabase, Neo4j and Qdrant modules with mocked drivers."""
from types import SimpleNamespace

import psycopg
import pytest
from neo4j.exceptions import ServiceUnavailable

from app.db import neo4j_db, supabase_db
from app.db.errors import DatabaseUnavailable
from app.db.neo4j_db import Neo4jGraph
from app.db.qdrant_db import QdrantStore
from app.db.supabase_db import SupabaseRepository
from app.services.policy_retriever import GeminiEmbedder, PolicyRetriever, build_policy_query
from app.services.reason_codes import graph_codes, supported_codes
from tests.conftest import GRAPH, TRANSACTION


# ----------------------------------------------------------------- Supabase

class FakeCursor:
    def __init__(self, row, hits):
        self.row, self.hits, self.executed = row, hits, []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.hits


class FakeConnection:
    def __init__(self, cursor):
        self._cursor, self.read_only = cursor, False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def cursor(self):
        return self._cursor


def test_get_transaction_success(monkeypatch):
    from datetime import datetime, timezone
    from decimal import Decimal
    row = {"transaction_id": "TX_1", "customer_id": "C_1", "device_id": "D_1",
           "transaction_amount": Decimal("10.50"),
           "transaction_time": datetime(2025, 11, 1, tzinfo=timezone.utc),
           "reason_codes": ["R01_NEW_DEVICE"], "feature_version": "v1"}
    cursor = FakeCursor(row, [])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(supabase_db.psycopg, "connect", lambda *a, **k: connection)

    tx = SupabaseRepository("postgresql://unused").get_transaction("TX_1")

    assert tx["transaction_amount"] == 10.5
    assert tx["transaction_time"] == "2025-11-01T00:00:00+00:00"
    assert tx["features_available"] is True and tx["rule_hits"] == []
    assert connection.read_only is True
    sql, params = cursor.executed[0]
    assert params == {"transaction_id": "TX_1"}          # parameterized, not string-formatted
    assert "labels" not in sql                            # the fraud label is never read


def test_get_transaction_not_found(monkeypatch):
    monkeypatch.setattr(supabase_db.psycopg, "connect", lambda *a, **k: FakeConnection(FakeCursor(None, [])))
    assert SupabaseRepository("postgresql://unused").get_transaction("TX_404") is None


def test_supabase_connection_error(monkeypatch):
    def fail(*a, **k):
        raise psycopg.OperationalError("password=secret123 host=db")
    monkeypatch.setattr(supabase_db.psycopg, "connect", fail)
    with pytest.raises(DatabaseUnavailable) as info:
        SupabaseRepository("postgresql://user:secret123@db/x").get_transaction("TX_1")
    assert "secret123" not in str(info.value)


# ----------------------------------------------------------------- Neo4j

def graph_with_fake_queries(responses):
    graph = Neo4jGraph.__new__(Neo4jGraph)
    graph.lookback_days, graph.label_splits, graph.max_records = 90, ["warmup", "train"], 25
    graph.calls = []

    def fake_query(cypher, **params):
        graph.calls.append((cypher, params))
        return responses.get(cypher, [])
    graph._query = fake_query
    return graph


def test_neighborhood_uses_target_payment_time_as_cutoff():
    history = GRAPH["customer_history"]
    graph = graph_with_fake_queries({
        neo4j_db.TARGET_PAYMENT: [{"time": "2025-11-01T01:30:00+00:00", "device_id": "D_1",
                                   "amount": 10.0, "merchant_id": "M_1"}],
        neo4j_db.CUSTOMER_HISTORY: [history],
        neo4j_db.DEVICE_OTHER_CUSTOMERS: GRAPH["device_other_customers"],
        neo4j_db.MERCHANT_PROFILE: [dict(GRAPH["merchant_profile"])],
        neo4j_db.BASELINE_FRAUD_RATE: [{"labelled_payments": 1000, "known_fraud_payments": 5}],
    })

    evidence = graph.get_customer_neighborhood("C_1", "TX_1")

    assert evidence["customer_found"] and evidence["transaction_found_in_graph"]
    assert evidence["cutoff_time"] == "2025-11-01T01:30:00+00:00"
    assert len(evidence["device_other_customers"]) == 2
    assert evidence["merchant_profile"]["baseline_fraud_rate"] == 0.005
    for _, params in graph.calls[1:]:
        assert params["cutoff"].isoformat() == "2025-11-01T01:30:00+00:00"
        assert params["label_splits"] == ["warmup", "train"]
        assert params["limit"] == 25


def test_neighborhood_customer_missing_from_graph():
    graph = graph_with_fake_queries({})
    evidence = graph.get_customer_neighborhood("C_unknown", "TX_1")
    assert evidence["customer_found"] is False
    assert evidence["device_other_customers"] == [] and evidence["merchant_profile"] is None
    assert graph_codes(evidence) == {}


def test_every_graph_query_excludes_future_and_unmatured_labels():
    for cypher in [neo4j_db.CUSTOMER_KNOWN_FRAUD, neo4j_db.DEVICE_OTHER_CUSTOMERS,
                   neo4j_db.CUSTOMER_SHARED_DEVICES, neo4j_db.MERCHANT_PROFILE]:
        assert "< $cutoff" in cypher
        assert "label_available_at <= $cutoff" in cypher


def test_neo4j_connection_error():
    graph = Neo4jGraph.__new__(Neo4jGraph)
    graph._driver = SimpleNamespace(execute_query=lambda *a, **k: (_ for _ in ()).throw(ServiceUnavailable("down")))
    with pytest.raises(DatabaseUnavailable):
        graph.ping()


def test_graph_codes_from_evidence():
    codes = graph_codes(GRAPH)
    assert set(codes) == {"G01_SHARED_DEVICE", "G02_FRAUD_LINKED_DEVICE"}


def test_supported_codes_combine_features_graph_and_rules():
    tx = dict(TRANSACTION, rule_hits=[{"rule_code": "HR_BLOCKLIST_DEVICE", "action": "BLOCK",
                                       "list_type": "blocked_devices", "entity_id": "D_1", "reason": "test"}])
    supported = supported_codes(tx, GRAPH)
    assert {"R01_NEW_DEVICE", "R02_GEO_MISMATCH", "G01_SHARED_DEVICE", "HR_BLOCKLIST_DEVICE"} <= set(supported)
    assert supported["R01_NEW_DEVICE"]["source"] == "supabase.features"


# ----------------------------------------------------------------- Qdrant / policy retrieval

def fake_point(i):
    return SimpleNamespace(id=f"id-{i}", score=0.8 - i / 100, payload={
        "source_document": f"DOC_{i}", "title": f"T{i}", "document_type": "playbooks",
        "chunk_number": i, "chunk_count": 4, "topic": "device change", "regulator_theme": None,
        "split": "train", "text": f"text {i}"})


def test_qdrant_top_five_search():
    store = QdrantStore("https://localhost:6333", "unused", "sentinel_corpus2")
    captured = {}

    def query_points(collection, **kwargs):
        captured.update(kwargs, collection=collection)
        return SimpleNamespace(points=[fake_point(i) for i in range(kwargs["limit"])])
    store._client = SimpleNamespace(query_points=query_points)

    results = store.search([0.1] * 3072, top_k=5, document_types=["playbooks"])

    assert [r["rank"] for r in results] == [1, 2, 3, 4, 5]
    assert results[0]["source_document"] == "DOC_0" and results[0]["chunk_number"] == 0
    assert captured["collection"] == "sentinel_corpus2" and captured["limit"] == 5
    assert captured["query_filter"].must[0].key == "document_type"


def test_search_policy_passes_query_vector_and_filter():
    calls = {}

    class Embedder:
        def embed_query(self, text):
            calls["text"] = text
            return [0.0] * 3072

    class Store:
        def search(self, vector, top_k, document_types):
            calls.update(top_k=top_k, types=document_types)
            return [{"rank": 1}]

    retriever = PolicyRetriever(Embedder(), Store(), ["playbooks"])
    assert retriever.search_policy("shared device", top_k=5) == [{"rank": 1}]
    assert calls == {"text": "shared device", "top_k": 5, "types": ["playbooks"]}


def test_embedding_dimension_mismatch_is_rejected():
    embedder = GeminiEmbedder.__new__(GeminiEmbedder)
    embedder.model, embedder.dimension, embedder.task_type = "gemini-embedding-2", 3072, "RETRIEVAL_QUERY"
    embedder._client = SimpleNamespace(models=SimpleNamespace(
        embed_content=lambda **k: SimpleNamespace(embeddings=[SimpleNamespace(values=[0.0] * 768)])))
    with pytest.raises(DatabaseUnavailable):
        embedder.embed_query("q")


def test_policy_query_mentions_signals_and_topics():
    query = build_policy_query(TRANSACTION, supported_codes(TRANSACTION, GRAPH))
    assert "device change" in query and "shared devices" in query
    assert "fraud_label" not in query
