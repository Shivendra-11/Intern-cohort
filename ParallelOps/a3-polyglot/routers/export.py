"""CSV export router — streams scored transactions from the file queue."""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()
BASE = Path(__file__).resolve().parent.parent
QUEUE = Path(os.environ.get("A3_QUEUE_DIR", BASE / "queue"))
RESULTS = QUEUE / "results"

COLUMNS = [
    "txn_id",
    "amount",
    "merchant",
    "location",
    "card_type",
    "timestamp",
    "score",
    "verdict",
]


def _read_results() -> list[dict]:
    rows: list[dict] = []
    if not RESULTS.is_dir():
        return rows
    for path in sorted(RESULTS.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        rows.append({**data, "txn_id": path.stem})
    return rows


@router.get("/transactions/export.csv", tags=["export"])
def export_transactions_csv() -> StreamingResponse:
    """Download all scored transactions as CSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for row in _read_results():
        writer.writerow([row.get(col, "") for col in COLUMNS])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )
