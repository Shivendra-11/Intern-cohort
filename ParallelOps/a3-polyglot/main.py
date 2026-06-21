"""A3 Polyglot — FastAPI ingest layer for the fraud-score system.

Pipeline (see contract.md):
  UI --POST /transaction--> FastAPI writes queue/incoming/<id>.json (stage queued)
  Node worker picks it up, writes queue/status/<id>.json (node_picked_up),
  runs the Rust engine, writes queue/results/<id>.json (scored).
  UI polls GET /transaction/<id>; FastAPI merges results -> status -> incoming.

State lives in the file-queue on disk (no broker, no database), so the three
language components stay decoupled. Written for Python 3.12.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from routers.audit import HIGH_RISK_THRESHOLD, maybe_append_high_risk
from routers.audit import router as audit_router
from routers.export import router as export_router
from routers.thresholds import router as thresholds_router

BASE = Path(__file__).resolve().parent

# Queue location is overridable so tests can use a temp dir (A3_QUEUE_DIR).
QUEUE = Path(os.environ.get("A3_QUEUE_DIR", BASE / "queue"))
INCOMING = QUEUE / "incoming"
STATUS = QUEUE / "status"
RESULTS = QUEUE / "results"


def _ensure_dirs() -> None:
    for d in (INCOMING, STATUS, RESULTS):
        d.mkdir(parents=True, exist_ok=True)


_ensure_dirs()

app = FastAPI(title="Fraud Score Ingest", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # the UI is opened from file://, so allow any origin
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(export_router)
app.include_router(thresholds_router)
app.include_router(audit_router)


# --- models / validation -----------------------------------------------------
class Transaction(BaseModel):
    """Incoming transaction. Pydantic enforces these; FastAPI returns 422 on failure."""
    amount: float = Field(..., gt=0, description="Positive transaction amount")
    merchant: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=100)
    card_type: Literal["credit", "debit", "prepaid"]
    timestamp: str = Field(..., description="ISO-8601, e.g. 2026-06-17T10:30:00Z")


class Enqueued(BaseModel):
    txn_id: str
    stage: str


class Status(BaseModel):
    txn_id: str
    stage: str  # queued | node_picked_up | scored
    score: int | None = None
    verdict: str | None = None
    factors: list[str] | None = None
    amount: float | None = None
    merchant: str | None = None
    location: str | None = None
    card_type: str | None = None
    timestamp: str | None = None


# --- helpers -----------------------------------------------------------------
def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- routes ------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/transaction", response_model=Enqueued, status_code=202)
def create_transaction(txn: Transaction) -> Enqueued:
    """Validate and enqueue a transaction for the Node worker to process."""
    _ensure_dirs()
    txn_id = uuid.uuid4().hex
    job = {"txn_id": txn_id, "stage": "queued", "enqueued_at": _now_iso(), **txn.model_dump()}
    (INCOMING / f"{txn_id}.json").write_text(json.dumps(job))
    return Enqueued(txn_id=txn_id, stage="queued")


@app.get("/transaction/{txn_id}", response_model=Status)
def get_transaction(txn_id: str) -> Status:
    """Merge results -> status -> incoming to report the current pipeline stage."""
    result = _read_json(RESULTS / f"{txn_id}.json")
    if result is not None:
        if result.get("score", 0) >= HIGH_RISK_THRESHOLD:
            maybe_append_high_risk({**result, "txn_id": txn_id})
        return Status(**{**result, "txn_id": txn_id, "stage": "scored"})

    status = _read_json(STATUS / f"{txn_id}.json")
    if status is not None:
        return Status(**{**status, "txn_id": txn_id, "stage": "node_picked_up"})

    incoming = _read_json(INCOMING / f"{txn_id}.json")
    if incoming is not None:
        return Status(**{**incoming, "txn_id": txn_id, "stage": "queued"})

    raise HTTPException(status_code=404, detail="unknown transaction id")


@app.get("/transactions", response_model=list[Status])
def list_transactions() -> list[Status]:
    """All scored transactions, newest first."""
    out: list[Status] = []
    for path in RESULTS.glob("*.json"):
        data = _read_json(path)
        if data is not None:
            out.append(Status(**{**data, "txn_id": path.stem, "stage": "scored"}))
    out.sort(key=lambda s: s.timestamp or "", reverse=True)
    return out


@app.get("/run-tests")
def run_tests() -> dict:
    """Run pytest + npm test + cargo test and aggregate pass/fail."""
    suites = [
        ("pytest", [sys.executable, "-m", "pytest", "-q"], BASE),
        ("npm test (worker)", ["npm", "test", "--silent"], BASE / "worker"),
        ("cargo test", ["cargo", "test", "--quiet"], BASE / "fraud-engine"),
    ]
    chunks: list[str] = []
    all_passed = True
    for name, cmd, cwd in suites:
        try:
            proc = subprocess.run(
                cmd, cwd=str(cwd), capture_output=True, text=True, timeout=180
            )
            ok = proc.returncode == 0
            all_passed = all_passed and ok
            chunks.append(
                f"### {name}: {'PASS' if ok else 'FAIL'}\n"
                + (proc.stdout or "")
                + (proc.stderr or "")
            )
        except Exception as exc:  # missing tool, timeout, etc.
            all_passed = False
            chunks.append(f"### {name}: ERROR\n{exc}")
    return {"passed": all_passed, "output": "\n\n".join(chunks)}
