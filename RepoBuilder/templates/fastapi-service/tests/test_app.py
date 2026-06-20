"""Tests for the ledger service. Run with: pytest"""
import pytest
from fastapi.testclient import TestClient

from app.main import app, reset_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_store():
    reset_store()
    yield
    reset_store()


def test_create_and_list_transaction():
    resp = client.post("/transactions", json={"amount": 100, "type": "credit"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert body["amount"] == 100
    assert body["type"] == "credit"

    listed = client.get("/transactions").json()
    assert len(listed) == 1
    assert listed[0]["id"] == 1


def test_invalid_input_is_rejected():
    # Negative amount violates gt=0.
    bad_amount = client.post("/transactions", json={"amount": -5, "type": "credit"})
    assert bad_amount.status_code == 422

    # Unknown type violates the Literal constraint.
    bad_type = client.post("/transactions", json={"amount": 5, "type": "wat"})
    assert bad_type.status_code == 422

    # Missing required field.
    missing = client.post("/transactions", json={"amount": 5})
    assert missing.status_code == 422


def test_balance_math():
    client.post("/transactions", json={"amount": 100, "type": "credit"})
    client.post("/transactions", json={"amount": 30, "type": "debit"})
    client.post("/transactions", json={"amount": 10, "type": "debit"})

    balance = client.get("/balance").json()
    assert balance["credits"] == 100
    assert balance["debits"] == 40
    assert balance["balance"] == 60
    assert balance["count"] == 3
