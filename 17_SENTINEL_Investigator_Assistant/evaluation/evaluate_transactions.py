"""End-to-end evaluation on 5 fraud + 5 genuine validation transactions.

    uv run python evaluation/evaluate_transactions.py                 # in-process app
    uv run python evaluation/evaluate_transactions.py --base-url http://127.0.0.1:8000

Labels are read ONLY here, after the API answered, to score the result.
The API never sees them: Supabase retrieval does not read public.labels, and the
graph only uses matured warmup/train labels from before each transaction.

Checks per response (independent of the app's own validation):
  * evidence grounding - every returned reason code is re-derived from the trace
  * citation validity  - every citation is one of the retrieved Qdrant chunks
  * action vs label    - flagged = MANUAL_REVIEW or ESCALATE (not a calibrated prediction)
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import httpx
import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.services.reason_codes import graph_codes  # noqa: E402

RESULTS_FILE = ROOT / "evaluation" / "transaction_results.json"
SEED = 42
PER_CLASS = 5

SELECTION_SQL = """
SELECT t.transaction_id, l.fraud_label
FROM public.transactions t
JOIN public.labels l USING (transaction_id)
WHERE t.split = 'validation'
ORDER BY t.transaction_id
"""


def select_transactions(db_url: str) -> dict[str, int]:
    """Reproducible pick: sort validation IDs, then random.Random(42).sample per class."""
    with psycopg.connect(db_url) as conn:
        rows = conn.execute(SELECTION_SQL).fetchall()
    rng = random.Random(SEED)
    fraud = rng.sample([tx for tx, label in rows if label == 1], PER_CLASS)
    genuine = rng.sample([tx for tx, label in rows if label == 0], PER_CLASS)
    return {**{tx: 1 for tx in fraud}, **{tx: 0 for tx in genuine}}


def grounding_failures(body: dict) -> list[str]:
    """Reason codes in the response that the traced evidence does not support."""
    trace = body["evidence_trace"]
    transaction, graph = trace["transaction"], trace["graph_evidence"]
    stored = set(transaction.get("reason_codes", []))
    derived_graph = set(graph_codes(graph))
    rules = {hit["rule_code"] for hit in transaction.get("rule_hits", [])}
    failures = []
    for finding in body["reason_codes"]:
        code = finding["code"]
        backed = (code in stored if code.startswith("R")
                  else code in derived_graph if code.startswith("G")
                  else code in rules)
        if not backed or not finding["evidence"]:
            failures.append(code)
    return failures


def citation_failures(body: dict) -> list[str]:
    retrieved = {(c["source_document"], c["chunk_number"]) for c in body["evidence_trace"]["policy_evidence"]}
    return [f"{c['source_document']}#{c['chunk_number']}" for c in body["citations"]
            if (c["source_document"], c["chunk_number"]) not in retrieved]


def make_client(base_url: str | None):
    if base_url:
        return httpx.Client(base_url=base_url, timeout=300)
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", help="Use a running server instead of the in-process app")
    args = parser.parse_args()

    settings = get_settings()
    selection = select_transactions(settings.supabase_db_url.get_secret_value())
    print("Selected:", selection)

    results = []
    with make_client(args.base_url) as client:
        for transaction_id, label in selection.items():
            started = time.perf_counter()
            response = client.post("/explain", json={"transaction_id": transaction_id, "include_trace": True})
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            body = response.json()
            record = {"transaction_id": transaction_id, "fraud_label": label,
                      "http_status": response.status_code, "client_elapsed_ms": elapsed_ms}
            if response.status_code == 200:
                llm_raw = body["evidence_trace"]["llm_raw_output"]
                record.update({
                    "recommended_action": body["recommended_action"],
                    "flagged": body["recommended_action"] != "ALLOW",
                    "risk_level": body["llm_interpretation"]["risk_level"],
                    "reason_codes": [f["code"] for f in body["reason_codes"]],
                    "supported_reason_codes": body["supported_reason_codes"],
                    "citations": [f"{c['source_document']}#{c['chunk_number']}" for c in body["citations"]],
                    "grounding_failures": grounding_failures(body),
                    "citation_failures": citation_failures(body),
                    "llm_proposed_unsupported_codes": body["validation"]["removed_reason_codes"],
                    "llm_proposed_invalid_citations": body["validation"]["removed_citations"],
                    "action_adjustments": body["validation"]["action_adjustments"],
                    "llm_used": body["models"].get("llm_used"),
                    "label_absent_from_evidence": "fraud_label" not in body["evidence_trace"]["transaction"],
                    "response": body,
                })
            else:
                record["error"] = body
            results.append(record)
            print(f"{transaction_id} label={label} status={response.status_code} "
                  f"action={record.get('recommended_action')} codes={record.get('reason_codes')} "
                  f"{elapsed_ms} ms")
            time.sleep(2)   # stay polite with free-tier rate limits

    ok = [r for r in results if r["http_status"] == 200]
    confusion = {"fraud_flagged": 0, "fraud_allowed": 0, "genuine_flagged": 0, "genuine_allowed": 0}
    for r in ok:
        confusion[f"{'fraud' if r['fraud_label'] else 'genuine'}_{'flagged' if r['flagged'] else 'allowed'}"] += 1
    summary = {
        "selection": {"split": "validation", "seed": SEED, "per_class": PER_CLASS,
                      "method": "sort validation IDs, random.Random(42).sample 5 fraud then 5 genuine"},
        "requests": len(results),
        "successful": len(ok),
        "errors": len(results) - len(ok),
        "evidence_grounding_failures": sum(len(r["grounding_failures"]) for r in ok),
        "citation_validation_failures": sum(len(r["citation_failures"]) for r in ok),
        "llm_unsupported_codes_removed_by_validation": sum(len(r["llm_proposed_unsupported_codes"]) for r in ok),
        "llm_invalid_citations_removed_by_validation": sum(len(r["llm_proposed_invalid_citations"]) for r in ok),
        "label_leak_checks_passed": all(r["label_absent_from_evidence"] for r in ok),
        "action_vs_label": confusion,
        "decision_rule": "flagged = MANUAL_REVIEW or ESCALATE; ALLOW = not flagged. Not a calibrated prediction.",
        "avg_processing_ms": int(sum(r["response"]["processing_time_ms"] for r in ok) / len(ok)) if ok else None,
        "max_processing_ms": max((r["response"]["processing_time_ms"] for r in ok), default=None),
        "llm_models_used": sorted({r["llm_used"] for r in ok}),
    }
    RESULTS_FILE.write_text(json.dumps({"summary": summary, "results": results}, indent=2, default=str),
                            encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Saved {RESULTS_FILE}")


if __name__ == "__main__":
    main()
