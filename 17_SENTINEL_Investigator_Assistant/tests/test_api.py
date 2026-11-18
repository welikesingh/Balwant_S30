"""HTTP layer with a fully faked investigation service."""
import pytest
from fastapi.testclient import TestClient

from app.db.errors import DatabaseUnavailable
from app.main import app
from app.services.investigation import InvestigationService
from app.services.llm_service import LLMUnavailable
from tests.conftest import FakeGraph, FakeLLM, FakePolicies, FakeTransactions


@pytest.fixture
def client_with():
    """Start the app with a fake service (so no real connections are opened)."""
    def make(**overrides):
        parts = {"transactions": FakeTransactions(), "graph": FakeGraph(),
                 "policies": FakePolicies(), "llm": FakeLLM(), **overrides}
        app.state.service = InvestigationService(**parts)
        return TestClient(app)
    yield make
    del app.state.service


def test_explain_success(client_with):
    with client_with() as client:
        response = client.post("/explain", json={"transaction_id": "TX_0000000001"})
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_action"] in {"ALLOW", "MANUAL_REVIEW", "ESCALATE"}
    assert body["citations"] and body["database_facts"]
    assert body["evidence_trace"] is None


def test_explain_not_found(client_with):
    with client_with() as client:
        response = client.post("/explain", json={"transaction_id": "TX_404"})
    assert response.status_code == 404
    assert response.json()["error"] == "transaction_not_found"


def test_explain_rejects_bad_input(client_with):
    with client_with() as client:
        assert client.post("/explain", json={"transaction_id": "x'; DROP TABLE t;--"}).status_code == 422
        assert client.post("/explain", json={}).status_code == 422


def test_explain_database_unavailable(client_with):
    with client_with(transactions=FakeTransactions(error=DatabaseUnavailable("Supabase connection failed"))) as client:
        response = client.post("/explain", json={"transaction_id": "TX_0000000001"})
    assert response.status_code == 503
    assert response.json()["error"] == "database_unavailable"


def test_explain_llm_unavailable(client_with):
    with client_with(llm=FakeLLM(error=LLMUnavailable("LLM API error 503"))) as client:
        response = client.post("/explain", json={"transaction_id": "TX_0000000001"})
    assert response.status_code == 502


def test_health_ok(client_with):
    with client_with() as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert set(response.json()["checks"]) == {"supabase", "neo4j", "qdrant"}


def test_health_reports_failed_database(client_with):
    with client_with(graph=FakeGraph(error=None)) as client:
        client.app.state.service.graph.ping = lambda: (_ for _ in ()).throw(DatabaseUnavailable("down"))
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"]["checks"]["neo4j"]["status"] == "unavailable"
