"""Contract tests for the FastAPI ingest layer.

These exercise the queue mechanics without needing the Node worker or Rust
binary running: the worker step is simulated by writing a result file directly.
Each test uses an isolated temp queue via the A3_QUEUE_DIR env var.
"""
import importlib
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("A3_QUEUE_DIR", str(tmp_path / "queue"))
    import main  # noqa: WPS433
    importlib.reload(main)  # re-read A3_QUEUE_DIR
    return TestClient(main.app), main


def _valid_payload(**overrides):
    base = {
        "amount": 4200.50,
        "merchant": "Acme Corp",
        "location": "NYC",
        "card_type": "credit",
        "timestamp": "2026-06-17T10:30:00Z",
    }
    base.update(overrides)
    return base


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_post_enqueues_and_returns_id(client):
    c, main = client
    r = c.post("/transaction", json=_valid_payload())
    assert r.status_code == 202
    body = r.json()
    assert body["stage"] == "queued"
    assert body["txn_id"]
    # the incoming file was written with all fields
    incoming = main.INCOMING / f"{body['txn_id']}.json"
    assert incoming.exists()
    assert json.loads(incoming.read_text())["merchant"] == "Acme Corp"


def test_get_reports_queued_then_scored(client):
    c, main = client
    txn_id = c.post("/transaction", json=_valid_payload()).json()["txn_id"]

    # before the worker runs -> queued
    s = c.get(f"/transaction/{txn_id}").json()
    assert s["stage"] == "queued"
    assert s["score"] is None

    # simulate the Node worker writing the Rust result
    result = {**_valid_payload(), "txn_id": txn_id, "score": 92,
              "verdict": "High Risk", "factors": ["amount", "prepaid"]}
    (main.RESULTS / f"{txn_id}.json").write_text(json.dumps(result))

    s2 = c.get(f"/transaction/{txn_id}").json()
    assert s2["stage"] == "scored"
    assert s2["score"] == 92
    assert s2["verdict"] == "High Risk"


def test_node_picked_up_stage(client):
    c, main = client
    txn_id = c.post("/transaction", json=_valid_payload()).json()["txn_id"]
    (main.STATUS / f"{txn_id}.json").write_text(json.dumps({"stage": "node_picked_up"}))
    assert c.get(f"/transaction/{txn_id}").json()["stage"] == "node_picked_up"


def test_unknown_id_is_404(client):
    c, _ = client
    assert c.get("/transaction/does-not-exist").status_code == 404


def test_transactions_lists_scored(client):
    c, main = client
    txn_id = c.post("/transaction", json=_valid_payload()).json()["txn_id"]
    result = {**_valid_payload(), "txn_id": txn_id, "score": 10, "verdict": "Low Risk"}
    (main.RESULTS / f"{txn_id}.json").write_text(json.dumps(result))
    rows = c.get("/transactions").json()
    assert len(rows) == 1
    assert rows[0]["score"] == 10


@pytest.mark.parametrize("bad", [
    {"amount": -5},                       # non-positive amount
    {"card_type": "bitcoin"},             # not in the allowed set
    {"merchant": ""},                     # empty merchant
])
def test_validation_rejects_bad_input(client, bad):
    c, _ = client
    r = c.post("/transaction", json=_valid_payload(**bad))
    assert r.status_code == 422
