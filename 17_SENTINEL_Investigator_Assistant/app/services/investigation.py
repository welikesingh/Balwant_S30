"""Investigation orchestrator: the Hybrid Graph RAG pipeline for one transaction.

    1. Supabase   -> transaction + features + hard-rule hits    (critical: fails the request)
    2. Neo4j      -> customer / device / merchant neighborhood   (optional: marked unavailable)
    3. Qdrant     -> top-5 policy chunks for a query built from 1 + 2
    4. Consolidate the evidence, derive SUPPORTED reason codes deterministically
    5. LLM        -> JSON explanation, validated with Pydantic
    6. Validate   -> drop unsupported codes and citations, apply action guardrails
"""
import logging
import time
from datetime import datetime
from typing import Any

from app.db.errors import DatabaseUnavailable
from app.models.schemas import (Citation, EvidenceStatus, InvestigationResponse, LLMExplanation,
                                LLMInterpretation, ReasonCodeFinding, ValidationReport)
from app.prompts.investigator_prompt import SYSTEM_INSTRUCTION, build_user_prompt
from app.services.policy_retriever import build_policy_query
from app.services.reason_codes import supported_codes

logger = logging.getLogger(__name__)

DISCLAIMER = ("Decision support only. The recommended action is an LLM judgement over retrieved "
              "evidence with rule-based guardrails; it is not a calibrated fraud probability. "
              "SENTINEL never blocks payments: a human investigator decides.")

ACTION_SEVERITY = {"ALLOW": 0, "MANUAL_REVIEW": 1, "ESCALATE": 2}


class TransactionNotFound(Exception):
    pass


# ----------------------------------------------------------------- facts written by code

def describe_transaction(t: dict[str, Any]) -> list[str]:
    facts = [
        f"Transaction {t['transaction_id']}: INR {t['transaction_amount']} via {t['payment_channel']} "
        f"to {t['merchant_category']} merchant {t['merchant_id']} ({t.get('merchant_name')}) "
        f"at {t['transaction_time']} (IST hour {t.get('hour_of_day')}).",
        f"Customer {t['customer_id']}: account age {t['account_age']} days, "
        f"{t['previous_transactions']} previous transactions, average value {t['average_transaction_value']}, "
        f"{t['failed_transactions']} failed attempts in the prior 24h.",
        f"Device {t.get('device_id') or 'unknown'} ({t.get('device_kind') or 'n/a'}); "
        f"is_new_device={t.get('is_new_device')}, "
        f"distinct_customers_per_device_7d={t.get('distinct_customers_per_device_7d')}.",
    ]
    if t.get("features_available"):
        facts.append(
            f"Features: amount_to_avg_ratio={t.get('amount_to_avg_ratio')}, is_new_city={t.get('is_new_city')}, "
            f"customer_merchant_distance_km={t.get('customer_merchant_distance_km')}, is_night={t.get('is_night')}, "
            f"txn_count_last_1h={t.get('txn_count_last_1h')}, combined_risk_flags={t.get('combined_risk_flags')}.")
        facts.append(f"Stored reason codes: {', '.join(t['reason_codes']) or 'none'}.")
    hits = t.get("rule_hits", [])
    facts.append("Hard-rule hits: " + (", ".join(f"{h['rule_code']} -> {h['action']}" for h in hits)
                                       if hits else "none") + ".")
    return facts


def describe_graph(graph: dict[str, Any] | None, status: str) -> list[str]:
    if graph is None:
        return ["Graph evidence unavailable (Neo4j could not be queried)."]
    if not graph["customer_found"]:
        return ["Customer not found in the graph: no relationship history."]
    h = graph["customer_history"]
    days = graph["lookback_days"]
    facts = [
        f"In the {days} days before this payment the customer made {h['payments_in_window']} payments to "
        f"{h['merchants_in_window']} merchants on {h['devices_in_window']} devices "
        f"({h['prior_payments_to_this_merchant']} to this merchant, {h['prior_payments_on_this_device']} on this device).",
    ]
    others = graph["device_other_customers"]
    recent = [c for c in others if c["payments_on_device_last_7d"] > 0]
    if graph.get("device_id"):
        facts.append(f"Device {graph['device_id']} was used by {len(others)} other customer(s) in the window, "
                     f"{len(recent)} of them in the last 7 days.")
    shared = graph["customer_shared_devices"]
    if shared:
        facts.append("Customer's other devices shared with other customers: "
                     + ", ".join(f"{d['device_id']} ({d['other_customers']} others)" for d in shared) + ".")
    facts.append(f"Earlier confirmed fraud payments by this customer (labels known before this payment): "
                 f"{len(graph['customer_known_fraud'])}.")
    m = graph.get("merchant_profile")
    if m:
        facts.append(f"Merchant {m['merchant_id']}: {m['payments_in_window']} payments in the window; "
                     f"confirmed fraud rate {m['known_fraud_rate']} on {m['labelled_payments']} matured labels "
                     f"(all-merchant baseline {m['baseline_fraud_rate']}).")
    if not graph["transaction_found_in_graph"]:
        facts.append("This transaction's PAID edge was not found in the graph; history uses its Supabase time.")
    return facts


def find_missing_information(transaction, graph_status, policy_status) -> list[str]:
    missing = ["No calibrated fraud model score is available for this payment."]
    if not transaction.get("features_available"):
        missing.append("Engineered features are missing for this transaction.")
    if not transaction.get("device_id"):
        missing.append("Device ID is missing, so device checks could not run.")
    if transaction.get("customer_location") is None:
        missing.append("Customer location is missing.")
    if transaction.get("features_available") and transaction.get("amount_to_avg_ratio") is None:
        missing.append("No prior payment history to compare the amount against.")
    if graph_status == "unavailable":
        missing.append("Neo4j graph evidence is unavailable.")
    elif graph_status == "customer_not_in_graph":
        missing.append("Customer has no graph history.")
    if policy_status == "unavailable":
        missing.append("Policy retrieval (Qdrant/Gemini embeddings) is unavailable.")
    elif policy_status == "no_results":
        missing.append("No policy chunks were retrieved.")
    return missing


# ----------------------------------------------------------------- validation

def validate_reason_codes(llm: LLMExplanation, supported: dict[str, dict[str, str]]):
    kept, removed = [], []
    for item in llm.reason_codes:
        code = item.code.strip().upper()
        if code not in supported:
            removed.append(f"{item.code}: not supported by retrieved evidence")
            continue
        if any(f.code == code for f in kept):
            continue
        entry = supported[code]
        kept.append(ReasonCodeFinding(code=code, description=entry["description"], source=entry["source"],
                                      evidence=entry["evidence"], llm_explanation=item.explanation))
    return kept, removed


def validate_citations(llm: LLMExplanation, chunks: list[dict[str, Any]]):
    retrieved = {(c["source_document"], int(c["chunk_number"])): c for c in chunks}
    kept, removed = [], []
    for item in llm.citations:
        key = (item.source_document.strip(), item.chunk_number)
        chunk = retrieved.get(key)
        if chunk is None:
            removed.append(f"{item.source_document}#{item.chunk_number}: not among retrieved chunks")
            continue
        if any((c.source_document, c.chunk_number) == key for c in kept):
            continue
        kept.append(Citation(source_document=chunk["source_document"], chunk_number=int(chunk["chunk_number"]),
                             title=chunk.get("title"), document_type=chunk.get("document_type"),
                             topic=chunk.get("topic"), rank=chunk["rank"], score=chunk["score"],
                             how_it_applies=item.how_it_applies))
    return kept, removed


def apply_action_guardrails(action: str, supported: dict, insufficient: bool) -> tuple[str, list[str]]:
    """Deterministic rules applied after the LLM. Returns (final action, notes)."""
    notes = []
    if "HR_BLOCKLIST_DEVICE" in supported and action != "ESCALATE":
        notes.append(f"{action} -> ESCALATE: device is on the blocked list (hard rule BLOCK is applied by "
                     "the rules engine / a human, never by the assistant).")
        action = "ESCALATE"
    elif "HR_ALLOWLIST_CUSTOMER" in supported and action == "ESCALATE":
        notes.append("ESCALATE -> MANUAL_REVIEW: allowlisted customer, hard rule caps the action at review.")
        action = "MANUAL_REVIEW"
    if insufficient and ACTION_SEVERITY[action] < ACTION_SEVERITY["MANUAL_REVIEW"]:
        notes.append("ALLOW -> MANUAL_REVIEW: evidence is incomplete, so the payment cannot be cleared.")
        action = "MANUAL_REVIEW"
    return action, notes


# ----------------------------------------------------------------- orchestrator

class InvestigationService:
    def __init__(self, transactions, graph, policies, llm, top_k: int = 5,
                 model_info: dict[str, str] | None = None):
        self.transactions = transactions   # SupabaseRepository
        self.graph = graph                 # Neo4jGraph
        self.policies = policies           # PolicyRetriever
        self.llm = llm                     # GeminiExplainer
        self.top_k = top_k
        self.model_info = model_info or {}

    def explain(self, transaction_id: str, include_trace: bool = False) -> InvestigationResponse:
        started = time.perf_counter()
        timings: dict[str, int] = {}

        def lap(name: str, since: float) -> float:
            now = time.perf_counter()
            timings[name] = int((now - since) * 1000)
            return now

        # 1. Transaction (critical). DatabaseUnavailable propagates to the API as 503.
        step = time.perf_counter()
        transaction = self.transactions.get_transaction(transaction_id)
        if transaction is None:
            raise TransactionNotFound(transaction_id)
        step = lap("supabase", step)

        # 2. Graph neighborhood (non-critical, but its absence is reported).
        graph, graph_status = None, "unavailable"
        try:
            graph = self.graph.get_customer_neighborhood(
                transaction["customer_id"], transaction_id,
                as_of=datetime.fromisoformat(transaction["transaction_time"]),
                device_id=transaction.get("device_id"), merchant_id=transaction.get("merchant_id"))
            graph_status = "ok" if graph["customer_found"] else "customer_not_in_graph"
        except DatabaseUnavailable as exc:
            logger.error("Graph evidence unavailable for %s: %s", transaction_id, exc)
        step = lap("neo4j", step)

        # 3. Policy retrieval with a query built from the evidence so far.
        supported = supported_codes(transaction, graph)
        policy_query = build_policy_query(transaction, supported)
        chunks, policy_status = [], "unavailable"
        try:
            chunks = self.policies.search_policy(policy_query, top_k=self.top_k)
            policy_status = "ok" if chunks else "no_results"
        except DatabaseUnavailable as exc:
            logger.error("Policy evidence unavailable for %s: %s", transaction_id, exc)
        step = lap("qdrant", step)

        # 4. Consolidated evidence (this is exactly what the LLM is allowed to use).
        investigation_context = {
            "transaction": transaction,
            "graph_evidence": graph,
            "policy_evidence": chunks,
        }
        insufficient = (graph_status == "unavailable" or policy_status != "ok"
                        or not transaction.get("features_available"))

        # 5. LLM reasoning. LLMUnavailable propagates to the API as 502.
        prompt = build_user_prompt(investigation_context["transaction"], investigation_context["graph_evidence"],
                                   graph_status, supported, investigation_context["policy_evidence"],
                                   policy_status)
        llm_result, attempts, llm_model_used = self.llm.explain(SYSTEM_INSTRUCTION, prompt)
        step = lap("llm", step)

        # 6. Validation against retrieved evidence.
        reason_findings, removed_codes = validate_reason_codes(llm_result, supported)
        citations, removed_citations = validate_citations(llm_result, chunks)
        action, adjustments = apply_action_guardrails(llm_result.recommended_action, supported, insufficient)

        missing = find_missing_information(transaction, graph_status, policy_status)
        missing += [m for m in llm_result.missing_information if m not in missing]

        timings["total"] = int((time.perf_counter() - started) * 1000)
        logger.info("explain %s action=%s codes=%s citations=%s removed=%d/%d timings=%s",
                    transaction_id, action, [f.code for f in reason_findings],
                    [f"{c.source_document}#{c.chunk_number}" for c in citations],
                    len(removed_codes), len(removed_citations), timings)

        trace = None
        if include_trace:
            trace = {**investigation_context, "supported_reason_codes": supported,
                     "llm_raw_output": llm_result.model_dump(), "timings_ms": timings}

        return InvestigationResponse(
            transaction_id=transaction_id,
            recommended_action=action,
            insufficient_evidence=insufficient,
            database_facts=describe_transaction(transaction) + describe_graph(graph, graph_status),
            supported_reason_codes=list(supported),
            reason_codes=reason_findings,
            llm_interpretation=LLMInterpretation(risk_level=llm_result.risk_level, summary=llm_result.summary,
                                                 investigation_steps=llm_result.investigation_steps),
            citations=citations,
            missing_information=missing,
            evidence_status=EvidenceStatus(transaction="ok",
                                           features="ok" if transaction.get("features_available") else "missing",
                                           graph=graph_status, policy=policy_status),
            validation=ValidationReport(removed_reason_codes=removed_codes, removed_citations=removed_citations,
                                        action_adjustments=adjustments, llm_attempts=attempts),
            policy_query=policy_query,
            models={**self.model_info, "llm_used": llm_model_used},
            processing_time_ms=timings["total"],
            disclaimer=DISCLAIMER,
            evidence_trace=trace,
        )
