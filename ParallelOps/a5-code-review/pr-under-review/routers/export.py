"""Buggy export route — missing auth (ISS-001)."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()
RESULTS = Path(__file__).resolve().parent.parent / "data" / "results"


@router.get("/transactions/export.csv")
def export_csv() -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["txn_id", "amount", "score"])
    if RESULTS.is_dir():
        for path in RESULTS.glob("*.json"):
            row = json.loads(path.read_text())
            writer.writerow([path.stem, row.get("amount"), row.get("score")])
    buffer.seek(0)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv")
