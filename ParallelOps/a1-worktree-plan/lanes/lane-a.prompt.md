# Lane A Agent Prompt — CSV Export Endpoint

## Context (read this before writing a single line of code)

You are working on the **A3 fraud-score system** located at
`a3-polyglot/` inside the repository root
(`/Users/shivendrakeshari/Desktop/ParallelOps`). The system is a FastAPI service
(`a3-polyglot/main.py`) backed by a file-queue pipeline. Scored transaction
results are stored as individual JSON files under `queue/results/<txn_id>.json`.

You are working on branch **`feat/lane-a`** in a dedicated git worktree. You
must not touch any files outside your owned set. No other agent exists in your
view — do not leave TODOs for other lanes.

---

## Your goal

Implement `GET /transactions/export.csv` — an endpoint that returns all scored
transactions as a downloadable CSV file.

### Acceptance criteria

1. `GET /transactions/export.csv` returns HTTP 200 with
   `Content-Type: text/csv; charset=utf-8` and
   `Content-Disposition: attachment; filename="transactions.csv"`.
2. The CSV contains a header row followed by one data row per scored transaction
   (files in `queue/results/*.json`).
3. Column order is exactly:
   `txn_id,amount,merchant,location,card_type,timestamp,score,verdict`
4. If there are no scored transactions, the response is the header row only (no
   error).
5. All existing tests in `tests/test_api.py` continue to pass without
   modification.
6. Your new tests in `tests/test_export.py` all pass.
7. `ruff check a3-polyglot/routers/export.py a3-polyglot/tests/test_export.py`
   exits 0 (no lint errors).

---

## Files you OWN (the only files you may create or modify)

| Path (relative to repo root) | Action |
|-------------------------------|--------|
| `a3-polyglot/routers/export.py` | CREATE |
| `a3-polyglot/tests/test_export.py` | CREATE |

**That is the complete list.** Do not modify any other file, including
`a3-polyglot/main.py`. The router registration in `main.py` will be added by the
merge integrator after your branch is reviewed.

---

## Files you must NOT touch

- `a3-polyglot/main.py`
- `a3-polyglot/contract.md`
- `a3-polyglot/requirements.txt`
- `a3-polyglot/routers/thresholds.py` (may not exist yet — do not create it)
- `a3-polyglot/routers/audit.py` (may not exist yet — do not create it)
- `a3-polyglot/config/thresholds.json`
- `a3-polyglot/audit/log.jsonl`
- `a3-polyglot/tests/test_api.py`
- `a3-polyglot/tests/test_thresholds.py` (may not exist yet)
- `a3-polyglot/tests/test_audit.py` (may not exist yet)
- `a3-polyglot/fraud-engine/**`
- `a3-polyglot/worker/**`
- `a3-polyglot/ui/**`

---

## Implementation guidance

### Router skeleton

Create `a3-polyglot/routers/export.py` as an `APIRouter` with a single route.
Import the `QUEUE` / `RESULTS` path constants by re-reading them from the
environment variable `A3_QUEUE_DIR` (same pattern used in `main.py`). Do NOT
import `main` directly to avoid circular imports.

```python
# a3-polyglot/routers/export.py  (skeleton — fill in the body)
from __future__ import annotations
import csv, io, json, os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()
BASE = Path(__file__).resolve().parent.parent
QUEUE = Path(os.environ.get("A3_QUEUE_DIR", BASE / "queue"))
RESULTS = QUEUE / "results"

COLUMNS = ["txn_id", "amount", "merchant", "location",
           "card_type", "timestamp", "score", "verdict"]

@router.get("/transactions/export.csv", tags=["export"])
def export_transactions_csv() -> StreamingResponse:
    ...
```

Use Python's built-in `csv.writer` writing to an `io.StringIO` buffer, then
return a `StreamingResponse` with the correct media type and headers.

### Test skeleton

`tests/test_export.py` must **not** import or reload `main` (you cannot register
the router there). Mount `routers.export.router` on a minimal standalone app:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.export import router

@pytest.fixture()
def export_client(tmp_path, monkeypatch):
    monkeypatch.setenv("A3_QUEUE_DIR", str(tmp_path / "queue"))
    # populate tmp_path/queue/results/*.json as needed
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), tmp_path
```

Monkeypatch `A3_QUEUE_DIR` before importing `routers.export` (or reload that
module after setting the env var) so `RESULTS` points at the temp queue.
Tests must cover:

- No transactions present → header row only, status 200.
- One scored transaction → header + one data row, correct column values.
- `Content-Type` header contains `text/csv`.
- `Content-Disposition` header contains `attachment`.

---

## Commit convention

All commits on this branch must follow:

```
feat(export): <imperative summary under 72 chars>
```

Example: `feat(export): add GET /transactions/export.csv endpoint`

Do not mix unrelated changes in a single commit.

---

## How to run your tests locally

```bash
cd a3-polyglot
.venv/bin/python -m pytest tests/test_export.py -v
# Or run the full suite to confirm no regression:
.venv/bin/python -m pytest -q
```

Lint (bootstrap ruff once — see `constraints.md` §1):
```bash
.venv/bin/pip install 'ruff>=0.4'  # once per worktree
.venv/bin/ruff check routers/export.py tests/test_export.py
```

---

## Definition of done (checklist before opening PR)

- [ ] `a3-polyglot/routers/export.py` exists and contains the `router` object.
- [ ] `a3-polyglot/tests/test_export.py` exists with at least 4 test functions.
- [ ] `pytest tests/test_export.py` passes (all green).
- [ ] `pytest tests/test_api.py` still passes (no regression).
- [ ] `ruff check` exits 0 on both owned files.
- [ ] No modifications to any forbidden file (verify with `git diff main --name-only`).
- [ ] Branch is `feat/lane-a`; at least one commit with the correct prefix.
