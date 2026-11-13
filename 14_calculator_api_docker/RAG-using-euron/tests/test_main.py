"""Tests for the Calculator API."""

import pytest

from app.main import app


# Use starlette's TestClient for sync testing

@pytest.fixture
def sync_client():
    from starlette.testclient import TestClient
    # Reset history before each test
    from app import main
    main.history.clear()
    with TestClient(app) as tc:
        yield tc


# -- /health --

def test_health(sync_client):
    resp = sync_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# -- /add --

def test_add(sync_client):
    resp = sync_client.post("/add", json={"a": 2, "b": 3})
    assert resp.status_code == 200
    assert resp.json()["result"] == 5.0


def test_add_floats(sync_client):
    resp = sync_client.post("/add", json={"a": 1.5, "b": 2.5})
    assert resp.status_code == 200
    assert resp.json()["result"] == 4.0


def test_add_missing_fields(sync_client):
    resp = sync_client.post("/add", json={"a": 2})
    assert resp.status_code == 422


def test_add_non_number(sync_client):
    resp = sync_client.post("/add", json={"a": "two", "b": 3})
    assert resp.status_code == 422


# -- /subtract --

def test_subtract(sync_client):
    resp = sync_client.post("/subtract", json={"a": 10, "b": 4})
    assert resp.status_code == 200
    assert resp.json()["result"] == 6.0


def test_subtract_negative(sync_client):
    resp = sync_client.post("/subtract", json={"a": 3, "b": 7})
    assert resp.status_code == 200
    assert resp.json()["result"] == -4.0


# -- /multiply --

def test_multiply(sync_client):
    resp = sync_client.post("/multiply", json={"a": 3, "b": 4})
    assert resp.status_code == 200
    assert resp.json()["result"] == 12.0


def test_multiply_by_zero(sync_client):
    resp = sync_client.post("/multiply", json={"a": 100, "b": 0})
    assert resp.status_code == 200
    assert resp.json()["result"] == 0.0


# -- /divide --

def test_divide(sync_client):
    resp = sync_client.post("/divide", json={"a": 10, "b": 2})
    assert resp.status_code == 200
    assert resp.json()["result"] == 5.0


def test_divide_by_zero(sync_client):
    resp = sync_client.post("/divide", json={"a": 10, "b": 0})
    assert resp.status_code == 400
    assert "zero" in resp.json()["detail"].lower()


def test_divide_fractional(sync_client):
    resp = sync_client.post("/divide", json={"a": 7, "b": 2})
    assert resp.status_code == 200
    assert resp.json()["result"] == 3.5


# -- /power --

def test_power(sync_client):
    resp = sync_client.post("/power", json={"a": 2, "b": 8})
    assert resp.status_code == 200
    assert resp.json()["result"] == 256.0


def test_power_zero(sync_client):
    resp = sync_client.post("/power", json={"a": 5, "b": 0})
    assert resp.status_code == 200
    assert resp.json()["result"] == 1.0


def test_power_float(sync_client):
    resp = sync_client.post("/power", json={"a": 9.0, "b": 0.5})
    assert resp.status_code == 200
    assert abs(resp.json()["result"] - 3.0) < 1e-9


# -- /calculate --

def test_calculate_simple(sync_client):
    resp = sync_client.post("/calculate", json={"expression": "2 + 3"})
    assert resp.status_code == 200
    assert resp.json()["result"] == 5.0


def test_calculate_order_of_operations(sync_client):
    resp = sync_client.post("/calculate", json={"expression": "2 + 3 * 4"})
    assert resp.status_code == 200
    assert resp.json()["result"] == 14.0


def test_calculate_parentheses(sync_client):
    resp = sync_client.post("/calculate", json={"expression": "(2 + 3) * 4"})
    assert resp.status_code == 200
    assert resp.json()["result"] == 20.0


def test_calculate_division_by_zero(sync_client):
    resp = sync_client.post("/calculate", json={"expression": "1 / 0"})
    assert resp.status_code == 400
    assert "zero" in resp.json()["detail"].lower()


def test_calculate_invalid_expression(sync_client):
    resp = sync_client.post("/calculate", json={"expression": "abc"})
    assert resp.status_code == 400


def test_calculate_missing_expression(sync_client):
    resp = sync_client.post("/calculate", json={})
    assert resp.status_code == 422


def test_calculate_unsupported_function(sync_client):
    """Reject expressions with function calls (security test)."""
    resp = sync_client.post("/calculate", json={"expression": "import os"})
    assert resp.status_code == 400


# -- /history --

def test_history_empty(sync_client):
    resp = sync_client.get("/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_records_operations(sync_client):
    sync_client.post("/add", json={"a": 1, "b": 2})
    sync_client.post("/subtract", json={"a": 10, "b": 3})
    resp = sync_client.get("/history")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert items[0]["operation"] == "add"
    assert items[0]["result"] == 3.0
    assert items[1]["operation"] == "subtract"
    assert items[1]["result"] == 7.0


def test_history_keeps_last_20(sync_client):
    for i in range(25):
        sync_client.post("/add", json={"a": i, "b": 1})
    resp = sync_client.get("/history")
    items = resp.json()
    assert len(items) == 20
    # First item in the kept 20 should be the 6th operation (i=5)
    assert items[0]["operation"] == "add"


def test_history_includes_calculate(sync_client):
    sync_client.post("/calculate", json={"expression": "5 * 6"})
    resp = sync_client.get("/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["operation"] == "calculate"
    assert resp.json()[0]["result"] == 30.0
