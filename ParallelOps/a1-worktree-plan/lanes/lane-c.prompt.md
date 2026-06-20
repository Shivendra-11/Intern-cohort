# Lane C Agent Prompt — Audit Log (HIGH RISK Persistence)

## Context (read this before writing a single line of code)

You are working on the **A3 fraud-score system** located at
`a3-polyglot/` inside the repository root
(`/Users/shivendrakeshari/Desktop/ParallelOps`). The system is a FastAPI service
(`a3-polyglot/main.py`). When the Node worker scores a transaction it writes a
result JSON to `queue/results/<txn_id>.json`. Transactions with `score >= 71`
are classified as HIGH RISK (see `contract.md`).

You are working on branch **`feat/lane-c`** in a dedicated git worktree. You
must not touch any files outside your owned set. No other agent exists in your
view — do not leave TODOs for other lanes.

---

## Your goal

Implement an audit-log that persistently records every HIGH RISK transaction
(score >= 71). Each qualifying transaction is appended as a single JSON line to
`audit/log.jsonl`. Additionally, expose a `GET /audit/log` endpoint that returns
the full list of audit entries.

### Acceptance criteria

1. **Post-merge (integrator):** every call to `GET /transaction/{txn_id}` that
   resolves to a scored result with `score >= 71` triggers an append to
   `audit/log.jsonl` (see integration note below — you do not edit `main.py`).
   **On your lane branch:** prove `append_audit_entry` writes the correct JSON
   line and `GET /audit/log` returns persisted entries.
2. Each appended record is valid JSON on a single line with at least the fields:
   `txn_id`, `score`, `verdict`, `merchant`, `amount`, `timestamp`, `logged_at`
   (ISO-8601 UTC string).
3. `GET /audit/log` returns HTTP 200 with a JSON array of all audit entries
   (empty array `[]` if log is absent or empty).
4. `audit/log.jsonl` survives across service restarts (append-only file; never
   truncated by normal operation).
5. A `audit/.gitkeep` file is committed so the directory exists in the repo even
   before any runtime entries are written.
6. All existing tests in `tests/test_api.py` continue to pass without
   modification.
7. Your new tests in `tests/test_audit.py` all pass.
8. `ruff check a3-polyglot/routers/audit.py a3-polyglot/tests/test_audit.py`
   exits 0.

---

## Files you OWN (the only files you may create or modify)

| Path (relative to repo root) | Action |
|-------------------------------|--------|
| `a3-polyglot/routers/audit.py` | CREATE |
| `a3-polyglot/audit/.gitkeep` | CREATE (empty placeholder) |
| `a3-polyglot/audit/log.jsonl` | RUNTIME-CREATED (do not commit with content) |
| `a3-polyglot/tests/test_audit.py` | CREATE |

**That is the complete list.** Do not modify any other file, including
`a3-polyglot/main.py`. The router registration and the hook into
`get_transaction` will be added by the merge integrator after your branch is
reviewed.

---

## Files you must NOT touch

- `a3-polyglot/main.py`
- `a3-polyglot/contract.md`
- `a3-polyglot/requirements.txt`
- `a3-polyglot/routers/export.py` (may not exist yet — do not create it)
- `a3-polyglot/routers/thresholds.py` (may not exist yet — do not create it)
- `a3-polyglot/config/thresholds.json`
- `a3-polyglot/tests/test_api.py`
- `a3-polyglot/tests/test_export.py` (may not exist yet)
- `a3-polyglot/tests/test_thresholds.py` (may not exist yet)
- `a3-polyglot/fraud-engine/**`
- `a3-polyglot/worker/**`
- `a3-polyglot/ui/**`

---

## Implementation guidance

### Audit helper module

`a3-polyglot/routers/audit.py` should expose:

1. A `AUDIT_LOG` path constant (overridable via `A3_AUDIT_LOG` env var for
   test isolation).
2. An `append_audit_entry(data: dict) -> None` function that appends a single
   JSON line to the log file (creates directories if needed).
3. A FastAPI `APIRouter` with `GET /audit/log`.

```python
# a3-polyglot/routers/audit.py  (skeleton — fill in the body)
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()
BASE = Path(__file__).resolve().parent.parent
_DEFAULT_LOG = BASE / "audit" / "log.jsonl"
AUDIT_LOG = Path(os.environ.get("A3_AUDIT_LOG", _DEFAULT_LOG))

HIGH_RISK_THRESHOLD = 71  # score >= this value triggers an audit entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    with AUDIT_LOG.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


@router.get("/audit/log", tags=["audit"])
def get_audit_log() -> list:
    if not AUDIT_LOG.exists():
        return []
    entries = []
    for line in AUDIT_LOG.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries
```

### Integration note for the merge integrator

After merging lane-C, `main.py`'s `get_transaction` endpoint must call
`append_audit_entry` when the resolved stage is `"scored"` and
`score >= HIGH_RISK_THRESHOLD`. Example addition inside the scored branch:

```python
from routers.audit import append_audit_entry, HIGH_RISK_THRESHOLD
# inside get_transaction, after building the Status object:
if result.get("score", 0) >= HIGH_RISK_THRESHOLD:
    append_audit_entry({**result, "txn_id": txn_id})
```

Include this note in your PR description so the integrator knows exactly what
to add to `main.py`.

### Test guidance

`tests/test_audit.py` must **not** import or reload `main`. Mount
`routers.audit.router` on a minimal `FastAPI()` + `TestClient`, and monkeypatch
`routers.audit.AUDIT_LOG` to a path under `tmp_path`. Cover:

- `append_audit_entry` with a HIGH RISK record (score=92) appends a valid JSON
  line to the log file.
- `append_audit_entry` with a LOW RISK record (score=10) — call the function
  directly; confirm the record is written (the threshold guard lives in main.py,
  not in the helper itself).
- `GET /audit/log` returns `[]` when log file is absent.
- `GET /audit/log` returns the correct entries after appending two records.

---

## Commit convention

All commits on this branch must follow:

```
feat(audit): <imperative summary under 72 chars>
```

Example: `feat(audit): persist HIGH RISK transactions to audit/log.jsonl`

---

## How to run your tests locally

```bash
cd a3-polyglot
.venv/bin/python -m pytest tests/test_audit.py -v
# Full suite regression check:
.venv/bin/python -m pytest -q
```

Lint (bootstrap ruff once — see `constraints.md` §1):
```bash
.venv/bin/pip install 'ruff>=0.4'  # once per worktree
.venv/bin/ruff check routers/audit.py tests/test_audit.py
```

---

## Definition of done (checklist before opening PR)

- [ ] `a3-polyglot/routers/audit.py` exists with `append_audit_entry` and `router`.
- [ ] `a3-polyglot/audit/.gitkeep` committed (empty file).
- [ ] `a3-polyglot/tests/test_audit.py` exists with at least 4 test functions.
- [ ] `pytest tests/test_audit.py` passes (all green).
- [ ] `pytest tests/test_api.py` still passes (no regression).
- [ ] `ruff check` exits 0 on both owned source files.
- [ ] No modifications to any forbidden file (verify with `git diff main --name-only`).
- [ ] Branch is `feat/lane-c`; at least one commit with the correct prefix.
- [ ] PR description includes the integration note for `main.py`.
