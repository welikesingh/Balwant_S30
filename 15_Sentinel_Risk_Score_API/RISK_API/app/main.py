"""SENTINEL rules-only risk API.

    uvicorn app.main:app --port 8000
    GET  /health  status + active thresholds (no auth)
    POST /score   one transaction (section 10.2 request) -> risk score, level, decision and reason codes

Customer history (90-day average, known devices and cities, failed attempts in 24 h, account
creation date) is looked up from the SENTINEL feature store, so callers only send the transaction.

If SENTINEL_API_KEY is set, POST /score requires header  X-API-Key: <key>.
Every response carries X-Pod-Name / X-Node-Name so load tests can see which replica served it.
"""

from __future__ import annotations

import hmac
import logging
import os
import socket
import time
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, Field

# read <project root>/.env (SUPABASE_URL, SUPABASE_KEY, SENTINEL_API_KEY, ...) however the app is
# started; variables already set in the environment (docker -e, kubectl env) take precedence
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from app import rules  # noqa: E402  (rules reads SENTINEL_RULES_CONFIG at import)
from app.features import compute_features  # noqa: E402
from app.history import HistoryUnavailable, SupabaseHistoryStore  # noqa: E402

RULES_VERSION = "sentinel-rules-0.2.0"
# Kubernetes sets the hostname to the pod name; NODE_NAME comes from the downward API
POD_NAME = os.getenv("POD_NAME") or socket.gethostname()
NODE_NAME = os.getenv("NODE_NAME", "unknown")

logger = logging.getLogger(__name__)
app = FastAPI(title="SENTINEL Risk API", version=RULES_VERSION)
config = rules.load_config()


@lru_cache(maxsize=1)
def get_history_store() -> Optional[SupabaseHistoryStore]:
    return SupabaseHistoryStore.from_env()


@app.middleware("http")
async def add_served_by_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Pod-Name"] = POD_NAME
    response.headers["X-Node-Name"] = NODE_NAME
    return response


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    city: Optional[str] = None


class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    transaction_amount: float = Field(..., gt=0)
    merchant_category: Optional[str] = None
    transaction_time: AwareDatetime = Field(..., description="ISO 8601 with offset, e.g. 2025-11-14T03:12:44+05:30")
    device_id: Optional[str] = Field(None, description="Omit if unknown; R01 then cannot fire")
    customer_age: Optional[int] = Field(None, ge=0)
    customer_location: Optional[Location] = Field(None, description="Omit if unknown; R02 then cannot fire")
    merchant_location: Location
    account_age: Optional[int] = Field(None, ge=0, description="Days; looked up from the customer record if omitted")

    model_config = {"json_schema_extra": {"examples": [{
        "transaction_id": "TX_DEMO_01",
        "customer_id": "C_b90ff711ce3e3dba",
        "transaction_amount": 50000.00,
        "merchant_category": "electronics",
        "transaction_time": "2024-10-01T03:12:44+05:30",
        "device_id": "D_44be20",
        "customer_age": 52,
        "customer_location": {"lat": 19.08, "lon": 72.88, "city": "Mumbai"},
        "merchant_location": {"lat": 28.61, "lon": 77.20, "city": "Delhi"},
    }]}}


class ScoreResponse(BaseModel):
    transaction_id: str
    risk_score: float
    risk_level: str
    decision: str
    reason_codes: List[str]
    explanation: str
    features: dict = Field(..., description="Rule inputs derived from the request and the customer's history")
    decision_source: str = "RULES"
    rules_version: str = RULES_VERSION
    latency_ms: float


def check_api_key(x_api_key: Optional[str]) -> None:
    api_key = os.getenv("SENTINEL_API_KEY")
    if api_key and not hmac.compare_digest(x_api_key or "", api_key):
        raise HTTPException(status_code=401, detail="missing or invalid X-API-Key")


@app.get("/health")
def health(store=Depends(get_history_store)):
    return {
        "status": "ok",
        "rules_version": RULES_VERSION,
        "auth_required": bool(os.getenv("SENTINEL_API_KEY")),
        "history_store": store.name if store else "not configured",
        "pod_name": POD_NAME,
        "node_name": NODE_NAME,
        "config": config,
    }


@app.post("/score", response_model=ScoreResponse)
def score(txn: Transaction, x_api_key: Optional[str] = Header(None), store=Depends(get_history_store)):
    check_api_key(x_api_key)
    if store is None:
        raise HTTPException(status_code=503, detail="customer history store not configured (SUPABASE_URL / SUPABASE_KEY)")
    t0 = time.perf_counter()
    try:
        history = store.fetch(txn.customer_id, before=txn.transaction_time)
    except HistoryUnavailable as e:
        logger.error("%s", e)
        raise HTTPException(status_code=503, detail="customer history unavailable") from e
    if history is None:
        raise HTTPException(status_code=404, detail=f"unknown customer_id {txn.customer_id}")

    features = compute_features(txn.model_dump(), history)
    result = rules.score_transaction(features, config)
    return ScoreResponse(
        transaction_id=txn.transaction_id,
        features=features,
        latency_ms=round((time.perf_counter() - t0) * 1000, 3),
        **result,
    )
