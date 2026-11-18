"""Shared fakes. Unit tests never touch a real database or the LLM."""
import copy

import pytest

from app.models.schemas import LLMExplanation

TRANSACTION = {
    "transaction_id": "TX_0000000001", "customer_id": "C_1", "merchant_id": "M_1", "device_id": "D_1",
    "transaction_amount": 5815.52, "amount_paise": 581552, "payment_channel": "UPI",
    "merchant_category": "electronics", "transaction_time": "2025-11-01T01:30:00+00:00",
    "customer_age": 40, "customer_location": {"city": "Indore"}, "merchant_location": {"city": "Delhi"},
    "account_age": 400, "previous_transactions": 12, "average_transaction_value": 1692.16,
    "failed_transactions": 0, "split": "validation", "merchant_name": "Synthetic Merchant 000034",
    "device_kind": "mobile", "amount_to_avg_ratio": 3.4, "is_new_device": True, "is_new_city": False,
    "customer_merchant_distance_km": 668.7, "hour_of_day": 7, "is_night": False, "txn_count_last_1h": 0,
    "distinct_customers_per_device_7d": 0, "combined_risk_flags": 2,
    "reason_codes": ["R01_NEW_DEVICE", "R02_GEO_MISMATCH"], "feature_version": "sentinel-features-1.0.0",
    "features_available": True, "rule_hits": [],
}

GRAPH = {
    "customer_found": True, "transaction_found_in_graph": True,
    "cutoff_time": "2025-11-01T01:30:00+00:00", "lookback_days": 90, "label_policy": "test",
    "device_id": "D_1", "merchant_id": "M_1",
    "customer_history": {"home_city": "Indore", "region": "central", "payments_in_window": 6,
                         "merchants_in_window": 5, "devices_in_window": 2, "avg_amount_in_window": 1692.16,
                         "prior_payments_to_this_merchant": 0, "prior_payments_on_this_device": 0},
    "customer_known_fraud": [],
    "device_other_customers": [
        {"customer_id": "C_2", "payments_on_device": 3, "payments_on_device_last_7d": 2,
         "known_fraud_on_device": 1, "known_fraud_total": 1, "last_used": "2025-10-30T00:00:00Z"},
        {"customer_id": "C_3", "payments_on_device": 1, "payments_on_device_last_7d": 1,
         "known_fraud_on_device": 0, "known_fraud_total": 0, "last_used": "2025-10-31T00:00:00Z"},
    ],
    "customer_shared_devices": [],
    "merchant_profile": {"merchant_id": "M_1", "name": "Synthetic Merchant 000034", "category": "electronics",
                         "city": "Delhi", "payments_in_window": 150, "labelled_payments": 40,
                         "known_fraud_payments": 0, "known_fraud_rate": 0.0, "baseline_fraud_rate": 0.005},
}

CHUNKS = [
    {"rank": i + 1, "point_id": f"p{i}", "score": 0.76 - i / 100, "source_document": f"DOC_playbooks_000000{i}",
     "title": f"Playbook {i}", "document_type": "playbooks", "chunk_number": 1, "chunk_count": 4,
     "topic": "device change", "regulator_theme": None, "split": "train", "text": f"Policy text {i}"}
    for i in range(5)
]


def make_llm_output(**overrides) -> LLMExplanation:
    data = {
        "risk_level": "MEDIUM", "recommended_action": "MANUAL_REVIEW",
        "summary": "New device and shared device signals.",
        "reason_codes": [{"code": "R01_NEW_DEVICE", "explanation": "device is new"},
                         {"code": "G01_SHARED_DEVICE", "explanation": "2 other customers in 7 days"}],
        "citations": [{"source_document": "DOC_playbooks_0000000", "chunk_number": 1,
                       "how_it_applies": "says to verify device changes"}],
        "investigation_steps": ["Confirm the device with the customer."],
        "missing_information": [],
    }
    data.update(overrides)
    return LLMExplanation.model_validate(data)


class FakeTransactions:
    def __init__(self, transaction=TRANSACTION, error=None):
        self.transaction, self.error = copy.deepcopy(transaction), error

    def get_transaction(self, transaction_id):
        if self.error:
            raise self.error
        if self.transaction is None or transaction_id != self.transaction["transaction_id"]:
            return None
        return copy.deepcopy(self.transaction)

    def ping(self):
        return {"transactions": 1}


class FakeGraph:
    def __init__(self, graph=GRAPH, error=None):
        self.graph, self.error, self.calls = copy.deepcopy(graph), error, []

    def get_customer_neighborhood(self, customer_id, transaction_id=None, **kwargs):
        self.calls.append((customer_id, transaction_id, kwargs))
        if self.error:
            raise self.error
        return copy.deepcopy(self.graph)

    def ping(self):
        return {"paid": 1}


class FakeStore:
    def collection_info(self):
        return {"collection": "sentinel_corpus2", "points": 850}


class FakePolicies:
    def __init__(self, chunks=CHUNKS, error=None):
        self.chunks, self.error, self.queries = copy.deepcopy(chunks), error, []
        self.store = FakeStore()

    def search_policy(self, query, top_k=5):
        self.queries.append(query)
        if self.error:
            raise self.error
        return copy.deepcopy(self.chunks[:top_k])


class FakeLLM:
    def __init__(self, output=None, error=None):
        self.output, self.error, self.prompts = output or make_llm_output(), error, []

    def explain(self, system_instruction, user_prompt):
        self.prompts.append(user_prompt)
        if self.error:
            raise self.error
        return self.output, 1, "fake-llm"


@pytest.fixture
def fakes():
    return {"transactions": FakeTransactions(), "graph": FakeGraph(),
            "policies": FakePolicies(), "llm": FakeLLM()}
