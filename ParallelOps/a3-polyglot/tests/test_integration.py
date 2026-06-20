"""Cross-stack integration: FastAPI queue → worker logic → Rust engine → API readback."""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ENGINE_MANIFEST = ROOT / "fraud-engine" / "Cargo.toml"
ENGINE_BIN = ROOT / "fraud-engine" / "target" / "debug" / "fraud-engine"


def _ensure_engine() -> Path:
    if not ENGINE_BIN.exists():
        subprocess.run(
            ["cargo", "build", "--quiet", "--manifest-path", str(ENGINE_MANIFEST)],
            check=True,
            cwd=str(ROOT),
        )
    return ENGINE_BIN


def _run_engine(binary: Path, job: dict) -> dict:
    proc = subprocess.run(
        [str(binary)],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


@pytest.fixture()
def pipeline_client(tmp_path, monkeypatch):
    queue = tmp_path / "queue"
    audit_log = tmp_path / "audit" / "log.jsonl"
    monkeypatch.setenv("A3_QUEUE_DIR", str(queue))
    monkeypatch.setenv("A3_AUDIT_LOG", str(audit_log))
    import routers.audit as audit_mod
    import main

    importlib.reload(audit_mod)
    importlib.reload(main)
    monkeypatch.setattr(audit_mod, "AUDIT_LOG", audit_log)
    return TestClient(main.app), main, queue


def test_full_pipeline_fastapi_to_rust(pipeline_client):
    """POST → simulate worker + Rust score → GET returns scored + audit entry."""
    client, main_mod, queue = pipeline_client
    binary = _ensure_engine()

    payload = {
        "amount": 9000.0,
        "merchant": "Risky Shop",
        "location": "unknown",
        "card_type": "prepaid",
        "timestamp": "2026-06-17T03:00:00Z",
    }
    created = client.post("/transaction", json=payload)
    assert created.status_code == 202
    txn_id = created.json()["txn_id"]

    job = json.loads((main_mod.INCOMING / f"{txn_id}.json").read_text())
    scored = _run_engine(binary, job)
    result = {
        **job,
        "stage": "scored",
        "score": scored["score"],
        "verdict": scored["verdict"],
        "factors": scored.get("factors", []),
    }
    main_mod.RESULTS.mkdir(parents=True, exist_ok=True)
    (main_mod.RESULTS / f"{txn_id}.json").write_text(json.dumps(result))

    status = client.get(f"/transaction/{txn_id}").json()
    assert status["stage"] == "scored"
    assert status["score"] >= 71
    assert status["verdict"] == "High Risk"

    audit = client.get("/audit/log").json()
    assert any(e["txn_id"] == txn_id for e in audit)
