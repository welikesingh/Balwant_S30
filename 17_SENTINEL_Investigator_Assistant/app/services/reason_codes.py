"""Reason-code catalog and the deterministic rules that decide which codes are SUPPORTED.

The LLM may only use a code that this module marks as supported by retrieved evidence.

Sources
  R01-R08  Already computed by the SENTINEL feature pipeline and stored in
           Supabase features.reason_codes (definitions: supabase_db_kit/
           sql_scripts_report/11_reason_codes.sql). We read them, we do not recompute them.
  G01-G04  Graph indicators derived here from Neo4j evidence (thresholds below).
  HR_*     Hard rules from Supabase hard_rules + list_entries (rules_config.json).
"""
from typing import Any

# code -> (short description, evidence source, corpus topic used to build the policy query)
REASON_CODE_CATALOG: dict[str, dict[str, str]] = {
    "R01_NEW_DEVICE":      {"description": "Device not seen for this customer in the prior 90 days",
                            "source": "supabase.features", "topic": "device change"},
    "R02_GEO_MISMATCH":    {"description": "New city for the customer, or merchant more than 500 km away",
                            "source": "supabase.features", "topic": "location change"},
    "R03_ODD_HOUR":        {"description": "Payment between 00:00 and 05:00 IST",
                            "source": "supabase.features", "topic": "night activity"},
    "R04_FAILED_ATTEMPTS": {"description": "3 or more failed payment attempts in the previous 24 hours",
                            "source": "supabase.features", "topic": "payment retries"},
    "R05_AMOUNT_SPIKE":    {"description": "Amount at least 5x the customer's 90-day average",
                            "source": "supabase.features", "topic": "amount context"},
    "R06_NEW_ACCOUNT":     {"description": "Account younger than 30 days",
                            "source": "supabase.features", "topic": "new accounts"},
    "R07_VELOCITY":        {"description": "4 or more payment attempts in the previous hour",
                            "source": "supabase.features", "topic": "payment bursts"},
    "R08_HIGH_RISK_MCC":   {"description": "Merchant category is electronics, gaming or gift cards",
                            "source": "supabase.features", "topic": "risk explanations"},
    "G01_SHARED_DEVICE":   {"description": "Payment device used by 2+ other customers in the 7 days before",
                            "source": "neo4j", "topic": "shared devices"},
    "G02_FRAUD_LINKED_DEVICE": {"description": "A device used by this customer was used by another "
                                               "customer with a confirmed (already matured) fraud payment",
                                "source": "neo4j", "topic": "shared devices"},
    "G03_PRIOR_CONFIRMED_FRAUD": {"description": "Customer has an earlier payment confirmed as fraud "
                                                 "(label available before this payment)",
                                  "source": "neo4j", "topic": "customer verification"},
    "G04_MERCHANT_ELEVATED_FRAUD": {"description": "Merchant's confirmed fraud rate in the lookback window is "
                                                   "at least 3x the all-merchant rate (min. 3 fraud payments)",
                                    "source": "neo4j", "topic": "risk explanations"},
    "HR_BLOCKLIST_DEVICE":   {"description": "Device is on the blocked-devices list (hard rule action BLOCK)",
                              "source": "supabase.hard_rules", "topic": "device change"},
    "HR_ALLOWLIST_CUSTOMER": {"description": "Customer is on the allowlist (hard rule caps action at review)",
                              "source": "supabase.hard_rules", "topic": "customer verification"},
}

SHARED_DEVICE_MIN_OTHER_CUSTOMERS_7D = 2
MERCHANT_RATE_MULTIPLIER = 3.0
MERCHANT_MIN_FRAUD_PAYMENTS = 3


def feature_codes(transaction: dict[str, Any]) -> dict[str, str]:
    """R-codes stored in Supabase, with the feature values that triggered them."""
    t = transaction
    explanations = {
        "R01_NEW_DEVICE": f"is_new_device={t.get('is_new_device')}, device_id={t.get('device_id')}",
        "R02_GEO_MISMATCH": (f"is_new_city={t.get('is_new_city')}, "
                             f"customer_merchant_distance_km={t.get('customer_merchant_distance_km')}"),
        "R03_ODD_HOUR": f"hour_of_day={t.get('hour_of_day')} IST, is_night={t.get('is_night')}",
        "R04_FAILED_ATTEMPTS": f"failed_transactions={t.get('failed_transactions')} in prior 24h",
        "R05_AMOUNT_SPIKE": (f"amount_to_avg_ratio={t.get('amount_to_avg_ratio')} "
                             f"(amount {t.get('transaction_amount')}, avg {t.get('average_transaction_value')})"),
        "R06_NEW_ACCOUNT": f"account_age={t.get('account_age')} days",
        "R07_VELOCITY": f"txn_count_last_1h={t.get('txn_count_last_1h')}",
        "R08_HIGH_RISK_MCC": f"merchant_category={t.get('merchant_category')}",
    }
    return {code: explanations.get(code, "stored in features.reason_codes")
            for code in transaction.get("reason_codes", []) if code in REASON_CODE_CATALOG}


def graph_codes(graph: dict[str, Any] | None) -> dict[str, str]:
    """G-codes derived from Neo4j evidence. Returns {} when there is no graph evidence."""
    if not graph or not graph.get("customer_found"):
        return {}
    codes: dict[str, str] = {}

    recent_sharers = [c for c in graph.get("device_other_customers", [])
                      if c["payments_on_device_last_7d"] > 0]
    if len(recent_sharers) >= SHARED_DEVICE_MIN_OTHER_CUSTOMERS_7D:
        codes["G01_SHARED_DEVICE"] = (f"device {graph['device_id']} used by {len(recent_sharers)} other "
                                      f"customers in the 7 days before this payment")

    fraud_devices = {graph["device_id"] for c in graph.get("device_other_customers", [])
                     if c["known_fraud_on_device"] > 0}
    fraud_devices |= {d["device_id"] for d in graph.get("customer_shared_devices", [])
                      if d["known_fraud_payments"] > 0}
    if fraud_devices:
        codes["G02_FRAUD_LINKED_DEVICE"] = ("confirmed fraud payments by other customers on device(s) "
                                            + ", ".join(sorted(fraud_devices)))

    known_fraud = graph.get("customer_known_fraud", [])
    if known_fraud:
        codes["G03_PRIOR_CONFIRMED_FRAUD"] = (f"{len(known_fraud)} earlier confirmed fraud payment(s), "
                                              f"latest {known_fraud[0]['transaction_id']}")

    merchant = graph.get("merchant_profile")
    if merchant and merchant.get("known_fraud_rate") is not None and merchant.get("baseline_fraud_rate"):
        if (merchant["known_fraud_payments"] >= MERCHANT_MIN_FRAUD_PAYMENTS
                and merchant["known_fraud_rate"] >= MERCHANT_RATE_MULTIPLIER * merchant["baseline_fraud_rate"]):
            codes["G04_MERCHANT_ELEVATED_FRAUD"] = (
                f"merchant {merchant['merchant_id']} fraud rate {merchant['known_fraud_rate']:.4f} vs "
                f"baseline {merchant['baseline_fraud_rate']:.4f}")
    return codes


def rule_codes(transaction: dict[str, Any]) -> dict[str, str]:
    return {hit["rule_code"]: f"{hit['entity_id']} on list {hit['list_type']} ({hit['reason']})"
            for hit in transaction.get("rule_hits", []) if hit["rule_code"] in REASON_CODE_CATALOG}


def supported_codes(transaction: dict[str, Any], graph: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    """Every reason code backed by retrieved evidence: {code: {description, source, evidence}}."""
    supported = {}
    for source_codes in (feature_codes(transaction), graph_codes(graph), rule_codes(transaction)):
        for code, evidence in source_codes.items():
            entry = REASON_CODE_CATALOG[code]
            supported[code] = {"description": entry["description"], "source": entry["source"],
                               "evidence": evidence}
    return supported
