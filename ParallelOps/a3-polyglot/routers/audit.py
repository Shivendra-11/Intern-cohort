"""Audit log for HIGH RISK transactions (score >= 71)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()
BASE = Path(__file__).resolve().parent.parent
_DEFAULT_LOG = BASE / "audit" / "log.jsonl"
AUDIT_LOG = Path(os.environ.get("A3_AUDIT_LOG", _DEFAULT_LOG))

HIGH_RISK_THRESHOLD = 71


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _already_logged(txn_id: str) -> bool:
    if not AUDIT_LOG.exists():
        return False
    for line in AUDIT_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            if json.loads(line).get("txn_id") == txn_id:
                return True
        except json.JSONDecodeError:
            continue
    return False


def maybe_append_high_risk(data: dict) -> None:
    """Append once per txn_id when score meets the HIGH RISK threshold."""
    if data.get("score", 0) < HIGH_RISK_THRESHOLD:
        return
    txn_id = data.get("txn_id")
    if txn_id and _already_logged(txn_id):
        return
    append_audit_entry(data)


def append_audit_entry(data: dict) -> None:
    """Append one JSON line to AUDIT_LOG. Creates the file/dirs if needed."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "txn_id": data.get("txn_id"),
        "score": data.get("score"),
        "verdict": data.get("verdict"),
        "merchant": data.get("merchant"),
        "amount": data.get("amount"),
        "timestamp": data.get("timestamp"),
        "logged_at": _now_iso(),
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


@router.get("/audit/log", tags=["audit"])
def get_audit_log() -> list:
    if not AUDIT_LOG.exists():
        return []
    entries: list = []
    for line in AUDIT_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
