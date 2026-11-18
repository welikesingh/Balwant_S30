"""Transaction evidence from Supabase PostgreSQL.

Schema source: supabase_db_kit/sql/01_create_tables.sql (verified against the live database).

The fraud label lives in public.labels and is deliberately never read here:
the investigation must not see the answer it is trying to explain.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.db.errors import DatabaseUnavailable

logger = logging.getLogger(__name__)


# Transaction fields + engineered features (FE-01..FE-10) + merchant name.
# labels and payment_outcomes are not joined: the label is the answer, and the
# outcome is only known after the authorisation decision.
TRANSACTION_SQL = """
SELECT
    t.transaction_id, t.customer_id, t.merchant_id, t.device_id,
    t.transaction_amount, t.amount_paise, t.payment_channel, t.merchant_category,
    t.transaction_time, t.customer_age, t.customer_location, t.merchant_location,
    t.account_age, t.previous_transactions, t.average_transaction_value,
    t.failed_transactions, t.split,
    m.synthetic_name AS merchant_name,
    d.device_kind,
    f.feature_as_of, f.amount_to_avg_ratio, f.is_new_device,
    f.customer_merchant_distance_km, f.is_new_city, f.hour_of_day, f.is_night,
    f.has_recent_failures, f.is_new_account, f.txn_count_last_1h,
    f.txn_amount_last_24h_paise, f.distinct_customers_per_device_7d,
    f.combined_risk_flags, f.mcc_target_encoded_rate,
    f.missing_customer_location, f.missing_device, f.cold_start,
    f.reason_codes, f.feature_version
FROM public.transactions t
LEFT JOIN public.features  f ON f.transaction_id = t.transaction_id
LEFT JOIN public.merchants m ON m.merchant_id   = t.merchant_id
LEFT JOIN public.devices   d ON d.device_id     = t.device_id
WHERE t.transaction_id = %(transaction_id)s
"""

# Hard rules (blocked devices, allowlisted customers) that were in force at the
# time of the transaction.
LIST_HITS_SQL = """
SELECT r.code AS rule_code, r.action, e.list_type, e.entity_id, e.reason, e.effective_from
FROM public.hard_rules r
JOIN public.list_entries e ON e.list_type = r.expression->>'list'
WHERE r.enabled
  AND e.effective_from <= %(as_of)s
  AND (
        (r.expression->>'field' = 'device_id'   AND e.entity_id = %(device_id)s)
     OR (r.expression->>'field' = 'customer_id' AND e.entity_id = %(customer_id)s)
  )
ORDER BY r.priority DESC
"""


def _to_json_friendly(row: dict[str, Any]) -> dict[str, Any]:
    """Turn Decimal and datetime values into float / ISO strings for JSON output."""
    clean = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, datetime):
            value = value.isoformat()
        clean[key] = value
    return clean


class SupabaseRepository:
    def __init__(self, db_url: str, connect_timeout: int = 15):
        self._db_url = db_url
        self._connect_timeout = connect_timeout

    def _connect(self) -> psycopg.Connection:
        try:
            conn = psycopg.connect(self._db_url, connect_timeout=self._connect_timeout,
                                   row_factory=dict_row)
        except psycopg.Error as exc:
            # Never include the connection string in errors: it contains the password.
            raise DatabaseUnavailable(f"Supabase connection failed: {type(exc).__name__}") from exc
        conn.read_only = True   # this service only ever reads
        return conn

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        """Transaction + features + active hard-rule hits, or None if the ID is unknown."""
        try:
            with self._connect() as conn, conn.cursor() as cur:
                cur.execute(TRANSACTION_SQL, {"transaction_id": transaction_id})
                row = cur.fetchone()
                if row is None:
                    return None
                cur.execute(LIST_HITS_SQL, {
                    "as_of": row["transaction_time"],
                    "device_id": row["device_id"],
                    "customer_id": row["customer_id"],
                })
                rule_hits = [_to_json_friendly(hit) for hit in cur.fetchall()]
        except psycopg.Error as exc:
            raise DatabaseUnavailable(f"Supabase query failed: {type(exc).__name__}") from exc

        transaction = _to_json_friendly(row)
        transaction["reason_codes"] = transaction.get("reason_codes") or []
        transaction["features_available"] = transaction.get("feature_version") is not None
        transaction["rule_hits"] = rule_hits
        return transaction

    def ping(self) -> dict[str, Any]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM public.transactions")
            return {"transactions": cur.fetchone()["n"]}
