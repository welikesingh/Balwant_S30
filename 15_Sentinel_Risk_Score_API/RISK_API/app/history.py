"""Customer history lookup from the SENTINEL feature store (Supabase / PostgREST).

One request fetches the customer row plus every transaction in the look-back window before the
transaction being scored, each with its payment outcome:

    GET /rest/v1/customers?customer_id=eq.<id>
        &select=customer_id,created_at,transactions(..., payment_outcomes(status,outcome_time))
        &transactions.transaction_time=gte.<before - 90d>&transactions.transaction_time=lt.<before>

Settings: SUPABASE_URL, SUPABASE_KEY (already in .env), HISTORY_TIMEOUT_S (default 2).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 90
TXN_FIELDS = ("transaction_id,device_id,transaction_amount,transaction_time,customer_location,"
              "payment_outcomes(status,outcome_time)")


class HistoryUnavailable(Exception):
    """The feature store could not be reached or returned an error."""


@dataclass
class PastTransaction:
    transaction_id: str
    transaction_time: datetime
    amount: float
    device_id: Optional[str]
    city: Optional[str]
    outcome_status: Optional[str]      # SUCCESS / FAILED, None if no outcome recorded
    outcome_time: Optional[datetime]


@dataclass
class CustomerHistory:
    customer_id: str
    created_at: datetime
    transactions: List[PastTransaction] = field(default_factory=list)  # prior window, newest first


def _ts(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def parse_customer(row: Dict) -> CustomerHistory:
    txns = []
    for t in row.get("transactions") or []:
        outcome = t.get("payment_outcomes") or {}
        txns.append(PastTransaction(
            transaction_id=t["transaction_id"],
            transaction_time=_ts(t["transaction_time"]),
            amount=float(t["transaction_amount"]),
            device_id=t.get("device_id"),
            city=(t.get("customer_location") or {}).get("city"),
            outcome_status=outcome.get("status"),
            outcome_time=_ts(outcome.get("outcome_time")),
        ))
    return CustomerHistory(row["customer_id"], _ts(row["created_at"]), txns)


class SupabaseHistoryStore:
    name = "supabase"

    def __init__(self, url: str, key: str, timeout_s: float = 2.0):
        self.client = httpx.Client(
            base_url=url.rstrip("/") + "/rest/v1",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=timeout_s,
        )

    @classmethod
    def from_env(cls) -> Optional["SupabaseHistoryStore"]:
        url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
        if not (url and key):
            logger.warning("SUPABASE_URL / SUPABASE_KEY not set - customer history lookup disabled")
            return None
        return cls(url.strip(), key.strip(), float(os.getenv("HISTORY_TIMEOUT_S", "2")))

    def fetch(self, customer_id: str, before: datetime) -> Optional[CustomerHistory]:
        """History strictly before `before`; None if the customer does not exist."""
        since = before - timedelta(days=LOOKBACK_DAYS)
        params = [
            ("customer_id", f"eq.{customer_id}"),
            ("select", f"customer_id,created_at,transactions({TXN_FIELDS})"),
            ("transactions.transaction_time", f"gte.{since.isoformat()}"),
            ("transactions.transaction_time", f"lt.{before.isoformat()}"),
            ("transactions.order", "transaction_time.desc"),
        ]
        try:
            resp = self.client.get("/customers", params=params)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HistoryUnavailable(f"feature store lookup failed: {e}") from e
        rows = resp.json()
        return parse_customer(rows[0]) if rows else None
