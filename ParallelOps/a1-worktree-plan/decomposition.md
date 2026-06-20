# Feature Decomposition — Fraud-Score System Extensions

## Repository context

| Item | Path |
|------|------|
| **Primary repo (implementation target)** | repo root (ParallelOps) |
| **FastAPI service root** | `a3-polyglot/` |
| **Shared verification runner** | `shared/lib/verify.sh` |
| **Task deliverables folder** | `a1-worktree-plan/` |

### DevLinker analog (representative full-stack mapping)

The same three-lane split maps cleanly onto the DevLinker monorepo at
`/Users/shivendrakeshari/Desktop/Devliker_fullstack` if you prefer a product
context. This plan implements against `a3-polyglot/` because it is the eval
sample repo with an isolated FastAPI surface and file-queue pipeline.

| Lane | Capability (this plan) | DevLinker equivalent |
|------|------------------------|----------------------|
| A | `GET /transactions/export.csv` | Backend export route + FE download button on `ProjectsDashboard` |
| B | `GET/PUT /config/thresholds` | Backend settings API + `DevLinker-Frontend/src/pages/Settings.jsx` |
| C | HIGH RISK audit log + `GET /audit/log` | Backend audit middleware + admin audit viewer page |

DevLinker paths would split across `DevLinker-backend/src/routes/` and
`DevLinker-Frontend/src/` with `app.js` as the integrator-only hot file (same
pattern as `main.py` here). **This A1 plan uses `a3-polyglot/` paths only.**

---

## Feature summary

Three new capabilities are added to the A3 fraud-score FastAPI service:

1. **Lane A — CSV Export** — `GET /transactions/export.csv` streams all scored
   transactions as a CSV download.
2. **Lane B — Threshold Config** — `GET /config/thresholds` and
   `PUT /config/thresholds` allow operators to read and overwrite the fraud-band
   boundaries (Low/Medium/High Risk score ranges) at runtime.
3. **Lane C — Audit Log** — every transaction whose `score >= 71` (HIGH RISK) is
   appended as a newline-delimited JSON record to `audit/log.jsonl`.

Each capability is self-contained: it touches distinct source files and requires
no inter-lane coordination during development.

---

## Lane A — CSV Export

### Goal
Add `GET /transactions/export.csv` to the FastAPI layer so callers can download a
comma-separated list of all scored transactions.

### Files OWNED (may create or modify)
| Path | Action |
|------|--------|
| `a3-polyglot/routers/export.py` | CREATE — router module containing the CSV endpoint |
| `a3-polyglot/tests/test_export.py` | CREATE — pytest tests for the CSV endpoint |

### Files that MUST NOT be touched
- `a3-polyglot/main.py` — shared app entry point; only the merge commit may add
  the `include_router` call after lane-A merges first.
- `a3-polyglot/contract.md` — shared data contract; no edits without cross-lane
  sign-off.
- `a3-polyglot/routers/thresholds.py` — owned by Lane B.
- `a3-polyglot/routers/audit.py` — owned by Lane C.
- `a3-polyglot/tests/test_thresholds.py` — owned by Lane B.
- `a3-polyglot/tests/test_audit.py` — owned by Lane C.
- `a3-polyglot/audit/log.jsonl` — owned by Lane C.
- `a3-polyglot/fraud-engine/` — Rust crate; out of scope for all lanes.
- `a3-polyglot/worker/` — Node worker; out of scope for all lanes.

### Notes
- The router reads from `RESULTS` (queue/results/*.json) — the same source used by
  `GET /transactions`. No schema changes required.
- CSV column order: `txn_id, amount, merchant, location, card_type, timestamp,
  score, verdict`.
- Lane A merges first; `main.py` is patched in that merge commit via a clean
  `include_router` append that will not conflict with Lane B or C additions.

---

## Lane B — Threshold Config

### Goal
Add `GET /config/thresholds` and `PUT /config/thresholds` so operators can
inspect and update the fraud-band score boundaries at runtime without restarting
the service.

### Files OWNED (may create or modify)
| Path | Action |
|------|--------|
| `a3-polyglot/routers/thresholds.py` | CREATE — router with GET + PUT endpoints |
| `a3-polyglot/config/thresholds.json` | CREATE — persisted default threshold config |
| `a3-polyglot/tests/test_thresholds.py` | CREATE — pytest tests for threshold endpoints |

### Files that MUST NOT be touched
- `a3-polyglot/main.py` — patched by merge commit only.
- `a3-polyglot/contract.md` — shared data contract; no edits without cross-lane
  sign-off.
- `a3-polyglot/routers/export.py` — owned by Lane A.
- `a3-polyglot/routers/audit.py` — owned by Lane C.
- `a3-polyglot/tests/test_export.py` — owned by Lane A.
- `a3-polyglot/tests/test_audit.py` — owned by Lane C.
- `a3-polyglot/audit/log.jsonl` — owned by Lane C.
- `a3-polyglot/fraud-engine/` — out of scope.
- `a3-polyglot/worker/` — out of scope.

### Notes
- Config is stored at `a3-polyglot/config/thresholds.json`. Default bands mirror
  `contract.md`: low 0–30, medium 31–70, high 71–100.
- PUT body is validated with Pydantic; the file is overwritten atomically.
- Lane B merges second; the merge commit adds a second `include_router` call to
  `main.py` that will not conflict with Lane A's first addition.

---

## Lane C — Audit Log

### Goal
Append a JSON record to `audit/log.jsonl` for every scored transaction whose
`score >= 71` (HIGH RISK verdict). The append happens inside the existing
`create_transaction` / result-polling path — or, preferably, as a background task
triggered on `GET /transaction/{txn_id}` when a HIGH RISK result is first seen.

### Files OWNED (may create or modify)
| Path | Action |
|------|--------|
| `a3-polyglot/routers/audit.py` | CREATE — audit helper and optional GET /audit/log endpoint |
| `a3-polyglot/audit/.gitkeep` | CREATE — ensures `audit/` exists in git |
| `a3-polyglot/audit/log.jsonl` | RUNTIME only — never commit with content |
| `a3-polyglot/tests/test_audit.py` | CREATE — pytest tests for audit persistence |

### Files that MUST NOT be touched
- `a3-polyglot/main.py` — patched by merge commit only.
- `a3-polyglot/contract.md` — no edits without sign-off.
- `a3-polyglot/routers/export.py` — owned by Lane A.
- `a3-polyglot/routers/thresholds.py` — owned by Lane B.
- `a3-polyglot/config/thresholds.json` — owned by Lane B.
- `a3-polyglot/tests/test_export.py` — owned by Lane A.
- `a3-polyglot/tests/test_thresholds.py` — owned by Lane B.
- `a3-polyglot/fraud-engine/` — out of scope.
- `a3-polyglot/worker/` — out of scope.

### Notes
- `audit/log.jsonl` is created at runtime if absent; the directory must be
  committed as `audit/.gitkeep`.
- Each record written: `{ "txn_id", "score", "verdict", "merchant", "amount",
  "timestamp", "logged_at" }`.
- Lane C merges last; the merge commit adds the final `include_router` call and,
  if audit-on-read is chosen, a `BackgroundTask` hook inside `get_transaction`.

---

## File overlap analysis

| File | Lane A | Lane B | Lane C |
|------|--------|--------|--------|
| `main.py` | FORBIDDEN (merge only) | FORBIDDEN (merge only) | FORBIDDEN (merge only) |
| `contract.md` | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| `routers/export.py` | OWNS | forbidden | forbidden |
| `routers/thresholds.py` | forbidden | OWNS | forbidden |
| `routers/audit.py` | forbidden | forbidden | OWNS |
| `config/thresholds.json` | forbidden | OWNS | forbidden |
| `audit/.gitkeep` | forbidden | forbidden | OWNS |
| `audit/log.jsonl` | forbidden | forbidden | runtime only |
| `tests/test_export.py` | OWNS | forbidden | forbidden |
| `tests/test_thresholds.py` | forbidden | OWNS | forbidden |
| `tests/test_audit.py` | forbidden | forbidden | OWNS |

Zero overlapping owned files across lanes. The only merge-time coordination
needed is sequential `include_router` additions to `main.py`, which are handled
in the merge commits as described in `merge-plan.md`.
