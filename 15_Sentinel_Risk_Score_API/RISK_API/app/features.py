"""Derive the rule inputs from the incoming transaction plus the customer's stored history.

Definitions follow feature_catalogue.json in the sentinel-data bucket ("at authorisation,
before state update"): only events before transaction_time count, the current one never does.
"""

from __future__ import annotations

import math
from datetime import timedelta, timezone
from typing import Dict, Optional

from app.history import CustomerHistory

IST = timezone(timedelta(hours=5, minutes=30))
FAILED_WINDOW = timedelta(hours=24)


def haversine_km(a: Dict, b: Dict) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def compute_features(txn: Dict, history: CustomerHistory) -> Dict:
    """txn: the validated /score request as a dict (transaction_time is an aware datetime)."""
    t = txn["transaction_time"]
    prior = [p for p in history.transactions
             if p.transaction_time < t and p.transaction_id != txn["transaction_id"]]

    # FE-01: mean of the preceding 90 days; None when there is no history
    avg = sum(p.amount for p in prior) / len(prior) if prior else None
    # FE-02: unknown device -> None (no flag)
    device = txn.get("device_id")
    is_new_device = None if not device else device not in {p.device_id for p in prior}
    # FE-03: unknown customer location -> None (no flag)
    cust_loc, merch_loc = txn.get("customer_location"), txn["merchant_location"]
    distance = round(haversine_km(cust_loc, merch_loc), 2) if cust_loc else None
    city = (cust_loc or {}).get("city")
    is_new_city = None if not city else city not in {p.city for p in prior}
    # FE-05: failed outcomes received in the 24 h before this transaction
    failed = sum(1 for p in prior
                 if p.outcome_status == "FAILED" and p.outcome_time is not None
                 and t - FAILED_WINDOW <= p.outcome_time < t)
    # FE-06: complete days since account creation (caller's value wins if sent)
    account_age = txn.get("account_age")
    if account_age is None:
        account_age = (t - history.created_at).days

    return {
        "amount": txn["transaction_amount"],
        "avg_amount_90d": round(avg, 2) if avg is not None else None,
        "previous_transactions_90d": len(prior),
        "is_new_device": is_new_device,
        "distance_km": distance,
        "is_new_city": is_new_city,
        "hour": t.astimezone(IST).hour,           # FE-04: IST hour
        "failed_attempts": failed,
        "account_age_days": account_age,
    }


def amount_ratio(f: Dict) -> Optional[float]:
    avg = f.get("avg_amount_90d")
    return f["amount"] / avg if avg else None
