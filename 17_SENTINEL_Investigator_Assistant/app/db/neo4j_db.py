"""Customer / device / merchant graph evidence from Neo4j.

Graph model (same as NEO4J_Graph_CustMerchDevice/graph_loader.py, loaded from the
Supabase data by scripts/load_graph_from_supabase.py):

    (:Customer)-[:USED_DEVICE {first_seen, last_seen, tx_count, days}]->(:Device)
    (:Customer)-[:PAID {transaction_id, amount, time, fraud_label, channel, device_id,
                        label_available_at, split}]->(:Merchant)

Leakage rules applied by every query:
  * only payments strictly BEFORE the investigated transaction are used (p.time < $cutoff),
    so the investigated transaction itself is never historical evidence;
  * a fraud label is only used if it was already available at that moment
    (p.label_available_at <= $cutoff) and comes from an allowed split (warmup/train).
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable, AuthError
from neo4j.time import DateTime as Neo4jDateTime

from app.db.errors import DatabaseUnavailable

logger = logging.getLogger(__name__)

# A label is "known" at the cutoff only if it matured before it and is not from
# the validation/holdout splits.
KNOWN_FRAUD = ("p.fraud_label = 1 AND p.label_available_at <= $cutoff "
               "AND p.split IN $label_splits")

TARGET_PAYMENT = """
MATCH (c:Customer {customer_id: $customer_id})-[p:PAID {transaction_id: $transaction_id}]->(m:Merchant)
RETURN p.time AS time, p.device_id AS device_id, p.amount AS amount,
       m.merchant_id AS merchant_id
"""

CUSTOMER_HISTORY = """
MATCH (c:Customer {customer_id: $customer_id})
OPTIONAL MATCH (c)-[p:PAID]->(m:Merchant)
WHERE p.time >= $window_start AND p.time < $cutoff
RETURN c.home_city AS home_city, c.region AS region,
       count(p)                    AS payments_in_window,
       count(DISTINCT m)           AS merchants_in_window,
       count(DISTINCT p.device_id) AS devices_in_window,
       round(avg(p.amount), 2)     AS avg_amount_in_window,
       sum(CASE WHEN m.merchant_id = $merchant_id THEN 1 ELSE 0 END) AS prior_payments_to_this_merchant,
       sum(CASE WHEN p.device_id = $device_id THEN 1 ELSE 0 END)     AS prior_payments_on_this_device
"""

CUSTOMER_KNOWN_FRAUD = f"""
MATCH (c:Customer {{customer_id: $customer_id}})-[p:PAID]->(m:Merchant)
WHERE p.time < $cutoff AND {KNOWN_FRAUD}
RETURN p.transaction_id AS transaction_id, toString(p.time) AS time,
       p.amount AS amount, m.merchant_id AS merchant_id, p.device_id AS device_id
ORDER BY p.time DESC
LIMIT $limit
"""

# Other customers who paid with the investigated device before the cutoff.
DEVICE_OTHER_CUSTOMERS = f"""
MATCH (d:Device {{device_id: $device_id}})<-[:USED_DEVICE]-(other:Customer)-[p:PAID]->(:Merchant)
WHERE other.customer_id <> $customer_id
  AND p.device_id = $device_id
  AND p.time >= $window_start AND p.time < $cutoff
WITH other,
     count(p)                                                    AS payments_on_device,
     sum(CASE WHEN p.time >= $week_start THEN 1 ELSE 0 END)      AS payments_on_device_last_7d,
     sum(CASE WHEN {KNOWN_FRAUD} THEN 1 ELSE 0 END)              AS known_fraud_on_device,
     max(p.time)                                                 AS last_used
OPTIONAL MATCH (other)-[p:PAID]->()
WHERE p.time < $cutoff AND {KNOWN_FRAUD}
RETURN other.customer_id AS customer_id, payments_on_device, payments_on_device_last_7d,
       known_fraud_on_device, count(p) AS known_fraud_total, toString(last_used) AS last_used
ORDER BY payments_on_device_last_7d DESC, payments_on_device DESC, customer_id
LIMIT $limit
"""

# The customer's other recent devices that were also used by other customers.
CUSTOMER_SHARED_DEVICES = f"""
MATCH (c:Customer {{customer_id: $customer_id}})-[own:PAID]->()
WHERE own.time >= $window_start AND own.time < $cutoff
  AND own.device_id IS NOT NULL AND own.device_id <> coalesce($device_id, '')
WITH DISTINCT own.device_id AS device_id
MATCH (d:Device {{device_id: device_id}})<-[:USED_DEVICE]-(other:Customer)-[p:PAID]->()
WHERE other.customer_id <> $customer_id
  AND p.device_id = device_id
  AND p.time >= $window_start AND p.time < $cutoff
RETURN device_id, d.kind AS device_kind,
       count(DISTINCT other)                          AS other_customers,
       sum(CASE WHEN {KNOWN_FRAUD} THEN 1 ELSE 0 END) AS known_fraud_payments
ORDER BY other_customers DESC, device_id
LIMIT $limit
"""

MERCHANT_PROFILE = f"""
MATCH (m:Merchant {{merchant_id: $merchant_id}})
OPTIONAL MATCH (:Customer)-[p:PAID]->(m)
WHERE p.time >= $window_start AND p.time < $cutoff
RETURN m.merchant_id AS merchant_id, m.name AS name, m.category AS category, m.city AS city,
       count(p) AS payments_in_window,
       sum(CASE WHEN p.split IN $label_splits AND p.label_available_at <= $cutoff THEN 1 ELSE 0 END)
           AS labelled_payments,
       sum(CASE WHEN {KNOWN_FRAUD} THEN 1 ELSE 0 END) AS known_fraud_payments
"""

# Fraud rate over all merchants in the same window, as a baseline for the merchant.
BASELINE_FRAUD_RATE = f"""
MATCH (:Customer)-[p:PAID]->(:Merchant)
WHERE p.time >= $window_start AND p.time < $cutoff
  AND p.split IN $label_splits AND p.label_available_at <= $cutoff
RETURN count(p) AS labelled_payments, sum(CASE WHEN {KNOWN_FRAUD} THEN 1 ELSE 0 END) AS known_fraud_payments
"""


def _plain(value: Any) -> Any:
    """Neo4j temporal values -> ISO strings so the evidence is JSON friendly."""
    if isinstance(value, Neo4jDateTime):
        return value.iso_format()
    return value


def _rate(fraud: int, total: int) -> float | None:
    return round(fraud / total, 5) if total else None


class Neo4jGraph:
    def __init__(self, uri: str, user: str, password: str,
                 lookback_days: int = 90, label_splits: list[str] | None = None,
                 max_records: int = 25):
        self._driver = GraphDatabase.driver(uri, auth=(user, password),
                                            connection_timeout=10)
        self.lookback_days = lookback_days
        self.label_splits = label_splits or ["warmup", "train"]
        self.max_records = max_records

    def close(self) -> None:
        self._driver.close()

    def _query(self, cypher: str, **params) -> list[dict[str, Any]]:
        try:
            records, _, _ = self._driver.execute_query(cypher, params, routing_="r")
        except (ServiceUnavailable, AuthError, Neo4jError, OSError) as exc:
            raise DatabaseUnavailable(f"Neo4j query failed: {type(exc).__name__}") from exc
        return [{k: _plain(v) for k, v in record.data().items()} for record in records]

    def get_customer_neighborhood(self, customer_id: str, transaction_id: str | None = None,
                                  as_of: datetime | None = None,
                                  device_id: str | None = None,
                                  merchant_id: str | None = None) -> dict[str, Any]:
        """Graph evidence about a customer as it looked just before the investigated payment.

        The cutoff time is the investigated payment's own time when it is in the graph,
        otherwise `as_of` (e.g. the Supabase transaction_time), otherwise now.
        """
        target = None
        if transaction_id:
            rows = self._query(TARGET_PAYMENT, customer_id=customer_id, transaction_id=transaction_id)
            target = rows[0] if rows else None

        if target:
            cutoff = datetime.fromisoformat(target["time"])
            device_id = target["device_id"]
            merchant_id = target["merchant_id"]
        else:
            cutoff = as_of or datetime.now(timezone.utc)

        params = {
            "customer_id": customer_id,
            "device_id": device_id,
            "merchant_id": merchant_id,
            "cutoff": cutoff,
            "window_start": cutoff - timedelta(days=self.lookback_days),
            "week_start": cutoff - timedelta(days=7),
            "label_splits": self.label_splits,
            "limit": self.max_records,
        }

        history_rows = self._query(CUSTOMER_HISTORY, **params)
        customer_found = bool(history_rows)

        evidence: dict[str, Any] = {
            "customer_found": customer_found,
            "transaction_found_in_graph": target is not None,
            "cutoff_time": cutoff.isoformat(),
            "lookback_days": self.lookback_days,
            "label_policy": (f"fraud labels used only if available before the cutoff "
                             f"and from splits {self.label_splits}"),
            "device_id": device_id,
            "merchant_id": merchant_id,
            "customer_history": history_rows[0] if customer_found else None,
            "customer_known_fraud": [],
            "device_other_customers": [],
            "customer_shared_devices": [],
            "merchant_profile": None,
        }
        if not customer_found:
            return evidence

        evidence["customer_known_fraud"] = self._query(CUSTOMER_KNOWN_FRAUD, **params)
        evidence["customer_shared_devices"] = self._query(CUSTOMER_SHARED_DEVICES, **params)
        if device_id:
            evidence["device_other_customers"] = self._query(DEVICE_OTHER_CUSTOMERS, **params)

        if merchant_id:
            merchant_rows = self._query(MERCHANT_PROFILE, **params)
            baseline = self._query(BASELINE_FRAUD_RATE, **params)[0]
            if merchant_rows:
                merchant = merchant_rows[0]
                merchant["known_fraud_rate"] = _rate(merchant["known_fraud_payments"],
                                                     merchant["labelled_payments"])
                merchant["baseline_fraud_rate"] = _rate(baseline["known_fraud_payments"],
                                                        baseline["labelled_payments"])
                evidence["merchant_profile"] = merchant
        return evidence

    def ping(self) -> dict[str, Any]:
        rows = self._query("MATCH ()-[p:PAID]->() RETURN count(p) AS paid")
        return rows[0]
