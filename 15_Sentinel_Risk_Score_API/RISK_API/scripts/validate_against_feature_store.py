"""Replay stored transactions through POST /score and compare with the stored feature rows.

For each sampled transaction the API recomputes the features from history only, and the result
is checked against the `features` table (and the history columns on `transactions`) written by
the original SENTINEL feature pipeline.

    python scripts/validate_against_feature_store.py --n 300
"""

import argparse
import os
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")
os.environ.pop("SENTINEL_API_KEY", None)  # in-process client, no auth needed

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

RULE_CODES = {"R01_NEW_DEVICE", "R02_GEO_MISMATCH", "R03_ODD_HOUR", "R04_FAILED_ATTEMPTS",
              "R05_AMOUNT_SPIKE", "R06_NEW_ACCOUNT"}
FEATURE_COLS = ("amount_to_avg_ratio,is_new_device,customer_merchant_distance_km,is_new_city,"
                "hour_of_day,has_recent_failures,is_new_account,reason_codes")


def sample_rows(n: int, seed: int):
    rest = httpx.Client(base_url=os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1", timeout=60,
                        headers={"apikey": os.environ["SUPABASE_KEY"],
                                 "Authorization": "Bearer " + os.environ["SUPABASE_KEY"]})
    rng = random.Random(seed)
    rows = []
    # keyset sampling (ids are TX_0000000001..); large OFFSETs with an embed time out server-side
    for start in rng.sample(range(1, 110000, 50), max(1, n // 10)):
        r = rest.get("/transactions", params={"select": f"*,features({FEATURE_COLS})",
                                              "transaction_id": f"gte.TX_{start:010d}",
                                              "order": "transaction_id", "limit": 10})
        r.raise_for_status()
        rows += [x for x in r.json() if x.get("features")]
    return rows[:n]


def to_request(row):
    keep = ("transaction_id", "customer_id", "transaction_amount", "merchant_category",
            "transaction_time", "device_id", "customer_age", "customer_location", "merchant_location")
    return {k: row[k] for k in keep if row.get(k) is not None}


def compare(row, resp):
    exp, got = row["features"], resp["features"]
    ratio = got["amount"] / got["avg_amount_90d"] if got["avg_amount_90d"] else None
    checks = {
        "amount_to_avg_ratio": (exp["amount_to_avg_ratio"] is None and ratio is None) or (
            exp["amount_to_avg_ratio"] is not None and ratio is not None
            and abs(exp["amount_to_avg_ratio"] - ratio) <= 1e-3 * max(1, ratio)),
        "is_new_device": exp["is_new_device"] == got["is_new_device"],
        "distance_km": (exp["customer_merchant_distance_km"] is None and got["distance_km"] is None) or (
            None not in (exp["customer_merchant_distance_km"], got["distance_km"])
            and abs(exp["customer_merchant_distance_km"] - got["distance_km"]) <= 0.05),
        "is_new_city": exp["is_new_city"] == got["is_new_city"],
        "hour_of_day": exp["hour_of_day"] == got["hour"],
        "failed_transactions": row["failed_transactions"] == got["failed_attempts"],
        "has_recent_failures": exp["has_recent_failures"] == (got["failed_attempts"] >= 3),
        "account_age": row["account_age"] == got["account_age_days"],
        "reason_codes R01-R06": set(exp["reason_codes"]) & RULE_CODES == set(resp["reason_codes"]),
    }
    return checks


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=300)
    p.add_argument("--seed", type=int, default=7)
    a = p.parse_args()

    rows = sample_rows(a.n, a.seed)
    client = TestClient(app)

    def run(row):
        r = client.post("/score", json=to_request(row))
        return row, r.status_code, r.json()

    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(run, rows))

    errors = [(row["transaction_id"], code, body) for row, code, body in results if code != 200]
    mismatches, examples = Counter(), {}
    for row, code, body in results:
        if code != 200:
            continue
        for name, ok in compare(row, body).items():
            if not ok:
                mismatches[name] += 1
                examples.setdefault(name, (row["transaction_id"], row["features"], body["features"]))

    ok_rows = len(results) - len(errors)
    print(f"transactions replayed: {len(results)}   HTTP errors: {len(errors)}")
    for tid, code, body in errors[:5]:
        print(f"  {tid}: {code} {body}")
    for name in ("amount_to_avg_ratio", "is_new_device", "distance_km", "is_new_city", "hour_of_day",
                 "failed_transactions", "has_recent_failures", "account_age", "reason_codes R01-R06"):
        print(f"  {name:<22} {ok_rows - mismatches[name]:>4}/{ok_rows} match")
    for name, (tid, exp, got) in examples.items():
        print(f"\nfirst mismatch on {name}: {tid}\n  stored:   {exp}\n  computed: {got}")
    sys.exit(1 if errors or mismatches else 0)


if __name__ == "__main__":
    main()
