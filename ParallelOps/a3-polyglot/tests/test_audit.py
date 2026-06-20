"""Tests for audit log persistence and GET /audit/log."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def audit_client(tmp_path, monkeypatch):
    log_path = tmp_path / "audit" / "log.jsonl"
    import routers.audit as audit_mod

    importlib.reload(audit_mod)
    monkeypatch.setattr(audit_mod, "AUDIT_LOG", log_path)
    app = FastAPI()
    app.include_router(audit_mod.router)
    return TestClient(app), log_path, audit_mod


def test_append_high_risk_writes_json_line(audit_client):
    _, log_path, audit_mod = audit_client
    audit_mod.append_audit_entry(
        {
            "txn_id": "tx1",
            "score": 92,
            "verdict": "High Risk",
            "merchant": "Acme",
            "amount": 9000.0,
            "timestamp": "2026-06-17T03:00:00Z",
        }
    )
    assert log_path.exists()
    record = json.loads(log_path.read_text().strip())
    assert record["txn_id"] == "tx1"
    assert record["score"] == 92
    assert "logged_at" in record


def test_append_low_risk_still_writes(audit_client):
    _, log_path, audit_mod = audit_client
    audit_mod.append_audit_entry({"txn_id": "tx2", "score": 10, "verdict": "Low Risk"})
    assert log_path.exists()
    assert json.loads(log_path.read_text().strip())["score"] == 10


def test_get_audit_log_empty_when_missing(audit_client):
    client, log_path, _ = audit_client
    assert not log_path.exists()
    assert client.get("/audit/log").json() == []


def test_get_audit_log_returns_entries(audit_client):
    client, _, audit_mod = audit_client
    audit_mod.append_audit_entry({"txn_id": "a", "score": 80})
    audit_mod.append_audit_entry({"txn_id": "b", "score": 90})
    entries = client.get("/audit/log").json()
    assert len(entries) == 2
    assert {e["txn_id"] for e in entries} == {"a", "b"}


def test_maybe_append_high_risk_skips_duplicates(audit_client):
    _, log_path, audit_mod = audit_client
    payload = {"txn_id": "dup", "score": 92, "verdict": "High Risk"}
    audit_mod.maybe_append_high_risk(payload)
    audit_mod.maybe_append_high_risk(payload)
    lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1
