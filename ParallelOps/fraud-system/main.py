"""FastAPI ingestion layer for the polyglot fraud-scoring system."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
QUEUE = Path(os.environ.get("FRAUD_QUEUE_DIR", BASE / "queue"))
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Transaction(BaseModel):
    amount: float = Field(..., gt=0)
    merchant: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    card_type: Literal["credit", "debit", "prepaid"]
    timestamp: str = Field(..., min_length=1)


class Enqueued(BaseModel):
    txn_id: str
    stage: str


class Status(BaseModel):
    txn_id: str
    stage: str
    score: Optional[int] = None
    verdict: Optional[str] = None
    factors: Optional[List[str]] = None
    amount: Optional[float] = None
    merchant: Optional[str] = None
    location: Optional[str] = None
    card_type: Optional[str] = None
    timestamp: Optional[str] = None


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/transaction", response_model=Enqueued, status_code=202)
def create_transaction(txn: Transaction) -> Enqueued:
    _ensure_dirs()
    txn_id = str(uuid.uuid4())
    job = {"txn_id": txn_id, "stage": "queued", **txn.model_dump()}
    (INCOMING / f"{txn_id}.json").write_text(json.dumps(job))
    return Enqueued(txn_id=txn_id, stage="queued")


@app.get("/transaction/{txn_id}", response_model=Status)
def get_transaction(txn_id: str) -> Status:
    result = _read_json(RESULTS / f"{txn_id}.json")
    if result is not None:
        return Status(**{**result, "txn_id": txn_id, "stage": "scored"})

    status = _read_json(STATUS / f"{txn_id}.json")
    if status is not None:
        return Status(**{**status, "txn_id": txn_id, "stage": "node_picked_up"})

    incoming = _read_json(INCOMING / f"{txn_id}.json")
    if incoming is not None:
        return Status(**{**incoming, "txn_id": txn_id, "stage": "queued"})

    raise HTTPException(status_code=404, detail="unknown transaction id")


@app.get("/transactions", response_model=List[Status])
def list_transactions() -> List[Status]:
    seen: set[str] = set()
    out: List[Status] = []

    for path in RESULTS.glob("*.json"):
        data = _read_json(path)
        if data is not None:
            seen.add(path.stem)
            out.append(Status(**{**data, "txn_id": path.stem, "stage": "scored"}))

    for path in STATUS.glob("*.json"):
        if path.stem in seen:
            continue
        data = _read_json(path)
        if data is not None:
            seen.add(path.stem)
            out.append(Status(**{**data, "txn_id": path.stem, "stage": "node_picked_up"}))

    for path in INCOMING.glob("*.json"):
        if path.stem in seen:
            continue
        data = _read_json(path)
        if data is not None:
            out.append(Status(**{**data, "txn_id": path.stem, "stage": "queued"}))

    return out


@app.get("/run-tests")
def run_tests() -> dict:
    suites = [
        ("pytest", [sys.executable, "-m", "pytest", "-q"], BASE),
        ("npm test (worker)", ["npm", "test", "--prefix", "worker"], BASE),
        (
            "cargo test",
            ["cargo", "test", "--manifest-path", str(BASE / "fraud-engine" / "Cargo.toml")],
            BASE,
        ),
    ]
    chunks: List[str] = []
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
        except Exception as exc:
            all_passed = False
            chunks.append(f"### {name}: ERROR\n{exc}")
    return {"passed": all_passed, "output": "\n\n".join(chunks)}
