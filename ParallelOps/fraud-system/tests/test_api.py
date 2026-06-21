"""API contract tests and end-to-end integration (FastAPI → queue → Node → Rust)."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RUST_BIN = ROOT / "fraud-engine" / "target" / "debug" / "fraud-engine"


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


@pytest.fixture()
def client(tmp_path, monkeypatch):
    queue = tmp_path / "queue"
    monkeypatch.setenv("FRAUD_QUEUE_DIR", str(queue))
    import main

    importlib.reload(main)
    return TestClient(main.app), main


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
    incoming = main.INCOMING / f"{body['txn_id']}.json"
    assert incoming.exists()


@pytest.mark.parametrize(
    "bad",
    [
        {"amount": -5},
        {"card_type": "bitcoin"},
        {"merchant": ""},
    ],
)
def test_validation_rejects_bad_input(client, bad):
    c, _ = client
    r = c.post("/transaction", json=_valid_payload(**bad))
    assert r.status_code == 422


def test_get_unknown_id_404(client):
    c, _ = client
    assert c.get("/transaction/does-not-exist").status_code == 404


def test_end_to_end_integration(client, monkeypatch):
    if not RUST_BIN.exists():
        subprocess.run(
            ["cargo", "build"],
            cwd=str(ROOT / "fraud-engine"),
            check=True,
        )
    assert RUST_BIN.exists(), f"Rust binary missing at {RUST_BIN}"

    c, main = client
    high_risk = _valid_payload(
        amount=9000,
        merchant="Acme",
        location="unknown",
        card_type="prepaid",
        timestamp="2026-06-17T03:00:00Z",
    )
    txn_id = c.post("/transaction", json=high_risk).json()["txn_id"]

    env = os.environ.copy()
    env["FRAUD_QUEUE_DIR"] = str(main.QUEUE)
    proc = subprocess.run(
        ["node", "worker/index.js", "--once"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout

    body = c.get(f"/transaction/{txn_id}").json()
    assert body["stage"] == "scored"
    assert isinstance(body["score"], int)
    assert 0 <= body["score"] <= 100
    assert body["verdict"] == "High Risk"
    assert "large_amount" in (body.get("factors") or [])

    assert not (main.INCOMING / f"{txn_id}.json").exists()
    assert (main.RESULTS / f"{txn_id}.json").exists()
