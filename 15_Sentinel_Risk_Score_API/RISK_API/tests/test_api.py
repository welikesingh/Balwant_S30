from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.history import CustomerHistory, HistoryUnavailable, PastTransaction
from app.main import app, get_history_store

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2025, 11, 14, 14, 0, tzinfo=IST)
PUNE = {"lat": 18.52, "lon": 73.85, "city": "Pune"}
PUNE_SHOP = {"lat": 18.53, "lon": 73.86, "city": "Pune"}
DELHI = {"lat": 28.61, "lon": 77.20, "city": "Delhi"}


def past(minutes_ago, amount=1000.0, device="D_HOME", city="Pune", status="SUCCESS", tid=None):
    t = NOW - timedelta(minutes=minutes_ago)
    return PastTransaction(tid or f"TX_P{minutes_ago}", t, amount, device, city, status, t + timedelta(seconds=1))


class FakeStore:
    name = "fake"

    def __init__(self):
        self.customers = {}
        self.fail = False

    def fetch(self, customer_id, before):
        if self.fail:
            raise HistoryUnavailable("down")
        h = self.customers.get(customer_id)
        if h is None:
            return None
        window = [p for p in h.transactions if before - timedelta(days=90) <= p.transaction_time < before]
        return CustomerHistory(h.customer_id, h.created_at, window)


@pytest.fixture
def store():
    s = FakeStore()
    # regular customer: 2 years old, 1,000 average, home device and city, no failures
    s.customers["C_REG"] = CustomerHistory("C_REG", NOW - timedelta(days=730),
                                           [past(60 * 24 * d) for d in range(1, 11)])
    app.dependency_overrides[get_history_store] = lambda: s
    yield s
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("SENTINEL_API_KEY", raising=False)


client = TestClient(app)


def txn(**overrides):
    body = {"transaction_id": "TX_T1", "customer_id": "C_REG", "transaction_amount": 1200.0,
            "transaction_time": NOW.isoformat(), "device_id": "D_HOME",
            "customer_location": PUNE, "merchant_location": PUNE_SHOP}
    body.update(overrides)
    return {k: v for k, v in body.items() if v is not None}


def score(**overrides):
    r = client.post("/score", json=txn(**overrides))
    assert r.status_code == 200, r.text
    return r.json()


def test_health(store):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["history_store"] == "fake"


def test_regular_transaction_is_low_allow(store):
    r = score()
    assert r["reason_codes"] == []
    assert (r["risk_level"], r["decision"]) == ("LOW", "ALLOW")
    f = r["features"]
    assert f["avg_amount_90d"] == 1000.0 and f["previous_transactions_90d"] == 10
    assert f["is_new_device"] is False and f["is_new_city"] is False
    assert f["account_age_days"] == 730 and f["hour"] == 14


@pytest.mark.parametrize("overrides,code", [
    ({"device_id": "D_NEW"}, "R01_NEW_DEVICE"),
    ({"merchant_location": DELHI}, "R02_GEO_MISMATCH"),
    ({"transaction_time": NOW.replace(hour=3).isoformat()}, "R03_ODD_HOUR"),
    ({"transaction_amount": 5000.0}, "R05_AMOUNT_SPIKE"),
    ({"account_age": 6}, "R06_NEW_ACCOUNT"),
])
def test_each_rule_fires_alone(store, overrides, code):
    assert score(**overrides)["reason_codes"] == [code]


def test_new_city_fires_geo_even_when_close(store):
    # customer in a city never seen before, merchant next door
    r = score(customer_location={"lat": 12.97, "lon": 77.59, "city": "Bengaluru"},
              merchant_location={"lat": 12.98, "lon": 77.60, "city": "Bengaluru"})
    assert r["reason_codes"] == ["R02_GEO_MISMATCH"]
    assert r["features"]["is_new_city"] is True


def test_failed_attempts_counted_from_last_24h_only(store):
    h = store.customers["C_REG"]
    h.transactions += [past(m, status="FAILED") for m in (5, 30, 600)]   # within 24 h
    h.transactions.append(past(60 * 30, status="FAILED"))                # 30 h ago: ignored
    r = score()
    assert r["features"]["failed_attempts"] == 3
    assert r["reason_codes"] == ["R04_FAILED_ATTEMPTS"]


def test_history_after_transaction_time_is_ignored(store):
    # a huge later purchase must not change the average for an earlier transaction
    store.customers["C_REG"].transactions.append(past(-60, amount=1_000_000))
    assert score()["features"]["avg_amount_90d"] == 1000.0


def test_current_transaction_excluded_from_its_own_history(store):
    store.customers["C_REG"].transactions.append(past(0, amount=99_999, tid="TX_T1"))
    assert score()["features"]["previous_transactions_90d"] == 10


def test_account_age_from_customer_record_when_not_sent(store):
    store.customers["C_NEW"] = CustomerHistory("C_NEW", NOW - timedelta(days=6, hours=3), [])
    r = score(customer_id="C_NEW")
    assert r["features"]["account_age_days"] == 6
    assert "R06_NEW_ACCOUNT" in r["reason_codes"]


def test_cold_start_customer(store):
    # no history: device and city are new, no average so no amount spike
    store.customers["C_COLD"] = CustomerHistory("C_COLD", NOW - timedelta(days=400), [])
    r = score(customer_id="C_COLD", transaction_amount=90000)
    assert r["features"]["avg_amount_90d"] is None
    assert r["reason_codes"] == ["R01_NEW_DEVICE", "R02_GEO_MISMATCH"]


def test_unknown_device_and_location_do_not_fire(store):
    r = score(device_id=None, customer_location=None)
    assert r["features"]["is_new_device"] is None and r["features"]["distance_km"] is None
    assert r["reason_codes"] == []


def test_contract_sample_is_critical_block(store):
    h = store.customers["C_REG"]
    # 11h+ before NOW (14:00) = shortly before the 03:12 transaction
    h.transactions += [past(m, status="FAILED", amount=2350) for m in (660, 670, 680, 690)]
    r = score(transaction_id="TX98231", transaction_amount=50000.0, device_id="D_44be20",
              transaction_time=datetime(2025, 11, 14, 3, 12, 44, tzinfo=IST).isoformat(),
              merchant_location=DELHI, account_age=6)
    assert r["transaction_id"] == "TX98231"
    assert set(r["reason_codes"]) == {"R01_NEW_DEVICE", "R02_GEO_MISMATCH", "R03_ODD_HOUR",
                                      "R04_FAILED_ATTEMPTS", "R05_AMOUNT_SPIKE", "R06_NEW_ACCOUNT"}
    assert (r["risk_level"], r["decision"]) == ("CRITICAL", "BLOCK")
    assert "km from the merchant" in r["explanation"]


def test_unknown_customer_404(store):
    assert client.post("/score", json=txn(customer_id="C_NOPE")).status_code == 404


def test_store_down_503(store):
    store.fail = True
    assert client.post("/score", json=txn()).status_code == 503


def test_store_not_configured_503():
    app.dependency_overrides[get_history_store] = lambda: None
    try:
        assert client.post("/score", json=txn()).status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("bad", [
    {"transaction_amount": 0}, {"transaction_time": "2025-11-14T03:12:44"},  # no timezone
    {"merchant_location": {"lat": 200, "lon": 0}}, {"customer_id": None},
])
def test_invalid_input_rejected(store, bad):
    body = txn()
    body.update({k: v for k, v in bad.items() if v is not None})
    for k in [k for k, v in bad.items() if v is None]:
        body.pop(k)
    assert client.post("/score", json=body).status_code == 422


def test_api_key_enforced(store, monkeypatch):
    monkeypatch.setenv("SENTINEL_API_KEY", "secret")
    assert client.post("/score", json=txn()).status_code == 401
    assert client.post("/score", json=txn(), headers={"X-API-Key": "secret"}).status_code == 200
