"""Orchestrator and LLM-output validation."""
import json
from types import SimpleNamespace

import pytest

from app.db.errors import DatabaseUnavailable
from app.services.investigation import InvestigationService, TransactionNotFound
from app.services.llm_service import GeminiExplainer, LLMUnavailable
from tests.conftest import (FakeGraph, FakeLLM, FakePolicies, FakeTransactions, TRANSACTION,
                            make_llm_output)


def service(transactions=None, graph=None, policies=None, llm=None):
    return InvestigationService(transactions or FakeTransactions(), graph or FakeGraph(),
                                policies or FakePolicies(), llm or FakeLLM(), top_k=5)


def test_successful_investigation():
    llm = FakeLLM()
    result = service(llm=llm).explain("TX_0000000001", include_trace=True)

    assert result.recommended_action == "MANUAL_REVIEW"
    assert [c.code for c in result.reason_codes] == ["R01_NEW_DEVICE", "G01_SHARED_DEVICE"]
    assert result.reason_codes[0].evidence.startswith("is_new_device=True")   # evidence written by code
    assert result.citations[0].source_document == "DOC_playbooks_0000000"
    assert result.citations[0].score == 0.76
    assert result.evidence_status.graph == "ok" and result.evidence_status.policy == "ok"
    assert result.insufficient_evidence is False
    assert any("TX_0000000001" in fact for fact in result.database_facts)
    assert set(result.evidence_trace) >= {"transaction", "graph_evidence", "policy_evidence"}


def test_prompt_never_contains_fraud_label_or_split():
    llm = FakeLLM()
    service(llm=llm).explain("TX_0000000001")
    prompt = llm.prompts[0]
    assert "fraud_label" not in prompt
    assert '"split"' not in prompt
    assert "<policy_chunk" in prompt and "<graph_evidence" in prompt


def test_transaction_not_found():
    with pytest.raises(TransactionNotFound):
        service().explain("TX_9999999999")


def test_supabase_unavailable_is_not_hidden():
    with pytest.raises(DatabaseUnavailable):
        service(transactions=FakeTransactions(error=DatabaseUnavailable("down"))).explain("TX_0000000001")


def test_invalid_citations_are_removed():
    output = make_llm_output(citations=[
        {"source_document": "DOC_playbooks_0000000", "chunk_number": 1, "how_it_applies": "ok"},
        {"source_document": "DOC_invented_999", "chunk_number": 0, "how_it_applies": "made up"},
        {"source_document": "DOC_playbooks_0000000", "chunk_number": 7, "how_it_applies": "wrong chunk"},
    ])
    result = service(llm=FakeLLM(output)).explain("TX_0000000001")
    assert [(c.source_document, c.chunk_number) for c in result.citations] == [("DOC_playbooks_0000000", 1)]
    assert len(result.validation.removed_citations) == 2


def test_unsupported_reason_codes_are_removed():
    output = make_llm_output(reason_codes=[
        {"code": "R01_NEW_DEVICE", "explanation": "ok"},
        {"code": "R07_VELOCITY", "explanation": "not in features"},
        {"code": "MADE_UP_CODE", "explanation": "invented"},
    ])
    result = service(llm=FakeLLM(output)).explain("TX_0000000001")
    assert [c.code for c in result.reason_codes] == ["R01_NEW_DEVICE"]
    assert len(result.validation.removed_reason_codes) == 2


def test_missing_graph_evidence_forces_review():
    output = make_llm_output(recommended_action="ALLOW", reason_codes=[])
    result = service(graph=FakeGraph(error=DatabaseUnavailable("neo4j down")),
                     llm=FakeLLM(output)).explain("TX_0000000001")
    assert result.evidence_status.graph == "unavailable"
    assert result.insufficient_evidence is True
    assert result.recommended_action == "MANUAL_REVIEW"
    assert result.validation.action_adjustments
    assert "G01_SHARED_DEVICE" not in result.supported_reason_codes
    assert any("Neo4j" in m for m in result.missing_information)


def test_incomplete_graph_customer_not_found():
    graph = FakeGraph(graph={"customer_found": False, "transaction_found_in_graph": False,
                             "cutoff_time": "x", "lookback_days": 90, "device_id": "D_1", "merchant_id": "M_1",
                             "customer_history": None, "customer_known_fraud": [],
                             "device_other_customers": [], "customer_shared_devices": [],
                             "merchant_profile": None, "label_policy": "test"})
    result = service(graph=graph).explain("TX_0000000001")
    assert result.evidence_status.graph == "customer_not_in_graph"
    assert "G01_SHARED_DEVICE" not in [c.code for c in result.reason_codes]
    assert any("no graph history" in m for m in result.missing_information)


def test_missing_policy_evidence():
    output = make_llm_output(citations=[{"source_document": "DOC_playbooks_0000000", "chunk_number": 1,
                                         "how_it_applies": "hallucinated"}])
    llm = FakeLLM(output)
    result = service(policies=FakePolicies(chunks=[]), llm=llm).explain("TX_0000000001")
    assert result.evidence_status.policy == "no_results"
    assert result.citations == [] and result.validation.removed_citations
    assert result.insufficient_evidence is True
    assert "No policy chunks were retrieved" in llm.prompts[0]


def test_policy_store_unavailable():
    result = service(policies=FakePolicies(error=DatabaseUnavailable("qdrant down"))).explain("TX_0000000001")
    assert result.evidence_status.policy == "unavailable"
    assert result.citations == []


def test_blocklisted_device_is_escalated_not_blocked():
    tx = dict(TRANSACTION, rule_hits=[{"rule_code": "HR_BLOCKLIST_DEVICE", "action": "BLOCK",
                                       "list_type": "blocked_devices", "entity_id": "D_1", "reason": "test"}])
    output = make_llm_output(recommended_action="ALLOW")
    result = service(transactions=FakeTransactions(tx), llm=FakeLLM(output)).explain("TX_0000000001")
    assert result.recommended_action == "ESCALATE"


# ----------------------------------------------------------------- LLM schema validation

def explainer_returning(*texts):
    explainer = GeminiExplainer.__new__(GeminiExplainer)
    explainer.models, explainer.temperature, explainer.attempts_per_model = ["test"], 0.0, len(texts)
    replies = iter(texts)
    explainer._client = SimpleNamespace(models=SimpleNamespace(
        generate_content=lambda **k: SimpleNamespace(text=next(replies))))
    return explainer


def test_llm_valid_json_is_parsed():
    valid = make_llm_output().model_dump_json()
    result, attempts, model = explainer_returning(valid).explain("sys", "user")
    assert result.recommended_action == "MANUAL_REVIEW" and attempts == 1


def test_llm_invalid_json_is_retried_then_rejected():
    bad_action = json.loads(make_llm_output().model_dump_json())
    bad_action["recommended_action"] = "BLOCK_PAYMENT"
    with pytest.raises(LLMUnavailable):
        explainer_returning("not json", json.dumps(bad_action)).explain("sys", "user")


def test_llm_invalid_then_valid_succeeds_on_retry():
    result, attempts, model = explainer_returning("{}", make_llm_output().model_dump_json()).explain("sys", "user")
    assert attempts == 2 and result.risk_level == "MEDIUM"


def test_llm_falls_back_when_primary_is_overloaded():
    from google.genai import errors
    explainer = GeminiExplainer.__new__(GeminiExplainer)
    explainer.models, explainer.temperature, explainer.attempts_per_model = ["primary", "backup"], 0.0, 2
    valid = make_llm_output().model_dump_json()

    def generate_content(model, **kwargs):
        if model == "primary":
            raise errors.APIError(503, {"error": {"code": 503, "status": "UNAVAILABLE", "message": "busy"}})
        return SimpleNamespace(text=valid)
    explainer._client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))

    result, attempts, model = explainer.explain("sys", "user")
    assert model == "backup" and attempts == 2
