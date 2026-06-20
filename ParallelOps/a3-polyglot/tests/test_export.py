"""Tests for GET /transactions/export.csv."""
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
def export_client(tmp_path, monkeypatch):
    monkeypatch.setenv("A3_QUEUE_DIR", str(tmp_path / "queue"))
    import routers.export as export_mod

    importlib.reload(export_mod)
    app = FastAPI()
    app.include_router(export_mod.router)
    return TestClient(app), tmp_path, export_mod


def _write_result(tmp_path, export_mod, txn_id: str, **fields) -> None:
    results = tmp_path / "queue" / "results"
    results.mkdir(parents=True, exist_ok=True)
    payload = {
        "amount": 100.0,
        "merchant": "Acme",
        "location": "NYC",
        "card_type": "credit",
        "timestamp": "2026-06-17T10:30:00Z",
        "score": 42,
        "verdict": "Medium Risk",
        **fields,
    }
    (results / f"{txn_id}.json").write_text(json.dumps(payload))


def test_export_empty_returns_header_only(export_client):
    client, _, _ = export_client
    r = client.get("/transactions/export.csv")
    assert r.status_code == 200
    lines = r.text.strip().splitlines()
    assert len(lines) == 1
    assert "txn_id" in lines[0]


def test_export_one_transaction(export_client):
    client, tmp_path, export_mod = export_client
    _write_result(tmp_path, export_mod, "abc123", merchant="ShopCo", score=10)
    r = client.get("/transactions/export.csv")
    lines = r.text.strip().splitlines()
    assert len(lines) == 2
    assert "abc123" in lines[1]
    assert "ShopCo" in lines[1]
    assert ",10," in lines[1] or lines[1].endswith(",10")


def test_export_content_type_is_csv(export_client):
    client, _, _ = export_client
    r = client.get("/transactions/export.csv")
    assert "text/csv" in r.headers.get("content-type", "")


def test_export_content_disposition_attachment(export_client):
    client, _, _ = export_client
    r = client.get("/transactions/export.csv")
    assert "attachment" in r.headers.get("content-disposition", "").lower()
