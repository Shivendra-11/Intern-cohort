# Merge Plan — Fraud-Score System Extensions

## Branch names

| Lane | Branch |
|------|--------|
| A — CSV Export | `feat/lane-a` |
| B — Threshold Config | `feat/lane-b` |
| C — Audit Log | `feat/lane-c` |
| Integration target | `main` |

---

## Merge order

```
main  <--[merge 1]-- feat/lane-a   (CSV export; lane diff has zero main.py changes)
main  <--[merge 2]-- feat/lane-b   (threshold config; lane diff has zero main.py changes)
main  <--[merge 3]-- feat/lane-c   (audit log; lane diff has zero main.py changes)
        │
        └── after EACH merge: integrator commits a separate main.py wiring patch
            (append-only include_router + lane-C get_transaction hook)
```

**Rationale:** Lane branches never edit `main.py`, so git merges are
conflict-free on lane-owned files. Lane A merges first because it is the
smallest surface (router + test only) and establishes the integrator wiring
pattern. Lane B merges second; the integrator appends a second `include_router`
line below A's. Lane C merges last; the integrator adds the third router plus
the `get_transaction` audit hook once all router modules exist on `main`.

---

## Merge 1 — `feat/lane-a` into `main`

### Pre-merge checklist
```bash
# From repo root
git checkout main
git fetch origin
git log --oneline feat/lane-a  # confirm at least one feat(export): commit

# Verify lane owns only the allowed files
git diff main...feat/lane-a --name-only
# Expected output (only these two, plus any __pycache__ entries auto-excluded):
#   a3-polyglot/routers/export.py
#   a3-polyglot/tests/test_export.py

# Run tests on the lane branch
git checkout feat/lane-a
cd a3-polyglot && .venv/bin/python -m pytest -q && cd ..
```

### Merge command
```bash
git checkout main
git merge --no-ff feat/lane-a -m "feat(export): merge lane-a CSV export endpoint"
```

### Post-merge: patch main.py
After the merge commit, the integrator adds the router registration manually:

```bash
# Edit a3-polyglot/main.py — add after the existing imports block:
#   from routers.export import router as export_router
# Add after app definition:
#   app.include_router(export_router)
git add a3-polyglot/main.py
git commit -m "feat(export): register export router in main.py"
```

### Expected conflicts
None. Lane A does not touch `main.py` or any file touched by other lanes.

### Post-merge verification
```bash
cd a3-polyglot
.venv/bin/python -m pytest -q
bash ../shared/lib/verify.sh .
```
Both must exit 0. Spot-check the endpoint:
```bash
uvicorn main:app &
curl -s http://localhost:8000/transactions/export.csv | head -2
kill %1
```

---

## Merge 2 — `feat/lane-b` into `main`

### Pre-merge checklist
```bash
git checkout main
git log --oneline feat/lane-b  # confirm at least one feat(thresholds): commit

git diff main...feat/lane-b --name-only
# Expected:
#   a3-polyglot/routers/thresholds.py
#   a3-polyglot/config/thresholds.json
#   a3-polyglot/tests/test_thresholds.py

git checkout feat/lane-b
cd a3-polyglot && .venv/bin/python -m pytest -q && cd ..
```

### Merge command
```bash
git checkout main
git merge --no-ff feat/lane-b -m "feat(thresholds): merge lane-b threshold config endpoints"
```

### Post-merge: patch main.py
```bash
# Edit a3-polyglot/main.py — add after the export router import:
#   from routers.thresholds import router as thresholds_router
# Add after the export include_router call:
#   app.include_router(thresholds_router)
git add a3-polyglot/main.py
git commit -m "feat(thresholds): register thresholds router in main.py"
```

### Expected conflicts
`main.py` was patched after merge 1 to add `export_router`. Lane B does not
touch `main.py`, so git will report no conflict. The integrator applies the
second `include_router` addition by hand in the post-merge commit.

If a conflict does appear on `main.py` (e.g. because a developer accidentally
touched it on `feat/lane-b`), the resolution policy is:
- Keep ALL existing `include_router` calls.
- Append the new `include_router` call below the last existing one.
- Never remove lines that were added in a previous merge.

### Post-merge verification
```bash
cd a3-polyglot
.venv/bin/python -m pytest -q
bash ../shared/lib/verify.sh .
```
Spot-check:
```bash
uvicorn main:app &
curl -s http://localhost:8000/config/thresholds
curl -s -X PUT http://localhost:8000/config/thresholds \
     -H "Content-Type: application/json" \
     -d '{"low_max":25,"medium_max":65,"high_min":66}'
kill %1
```

---

## Merge 3 — `feat/lane-c` into `main`

### Pre-merge checklist
```bash
git checkout main
git log --oneline feat/lane-c  # confirm at least one feat(audit): commit

git diff main...feat/lane-c --name-only
# Expected:
#   a3-polyglot/routers/audit.py
#   a3-polyglot/audit/.gitkeep
#   a3-polyglot/tests/test_audit.py

git checkout feat/lane-c
cd a3-polyglot && .venv/bin/python -m pytest -q && cd ..
```

### Merge command
```bash
git checkout main
git merge --no-ff feat/lane-c -m "feat(audit): merge lane-c audit log feature"
```

### Post-merge: patch main.py
This patch is the most involved because it adds both an `include_router` call
and a hook inside the existing `get_transaction` function body.

```bash
# Edit a3-polyglot/main.py:
# 1. Add import after the thresholds router import:
#      from routers.audit import router as audit_router, append_audit_entry, HIGH_RISK_THRESHOLD
# 2. Add after the thresholds include_router call:
#      app.include_router(audit_router)
# 3. Inside get_transaction(), after the "result is not None" branch builds
#    the Status object, add:
#      if (result.get("score") or 0) >= HIGH_RISK_THRESHOLD:
#          append_audit_entry({**result, "txn_id": txn_id})
git add a3-polyglot/main.py
git commit -m "feat(audit): register audit router and hook HIGH RISK logging in main.py"
```

### Expected conflicts
`main.py` was edited after merge 2. Lane C does not touch `main.py`, so git
will report no conflict. The integrator applies all three edits by hand.

If a conflict does appear, the resolution policy is identical to merge 2:
retain all prior additions, append new ones, never delete existing lines.

### Post-merge verification
```bash
cd a3-polyglot
.venv/bin/python -m pytest -q
bash ../shared/lib/verify.sh .
```
Both must exit 0. Confirm the integrator `main.py` hook fires on HIGH RISK:
```bash
# Write a synthetic HIGH RISK result and poll GET /transaction
uvicorn main:app &
mkdir -p queue/results
echo '{"amount":9999,"merchant":"Shady","location":"XX","card_type":"prepaid","timestamp":"2026-06-17T03:00:00Z","score":92,"verdict":"High Risk"}' \
  > queue/results/audit-smoke.json
curl -s http://localhost:8000/transaction/audit-smoke
curl -s http://localhost:8000/audit/log | python3 -c "import sys,json; assert any(e.get('txn_id')=='audit-smoke' for e in json.load(sys.stdin))"
kill %1
```

---

## Full verification plan (run after ALL three merges)

```bash
cd /Users/shivendrakeshari/Desktop/ParallelOps/a3-polyglot

# 1. Python test suite (all lanes)
.venv/bin/python -m pytest -q
# Expected: all tests pass, 0 failures

# 2. Stack-aware runner
bash ../shared/lib/verify.sh .
# Expected: VERIFY: PASS

# 3. Endpoint smoke tests (requires running server)
uvicorn main:app --port 8001 &
SERVER_PID=$!

# Health
curl -sf http://localhost:8001/health

# CSV export
curl -sf http://localhost:8001/transactions/export.csv \
  | head -1 | grep -q "txn_id,amount"

# Threshold config read
curl -sf http://localhost:8001/config/thresholds \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['low_max']==30"

# Threshold config write
curl -sf -X PUT http://localhost:8001/config/thresholds \
  -H "Content-Type: application/json" \
  -d '{"low_max":20,"medium_max":60,"high_min":61}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['low_max']==20"

# Audit log read (may be empty on a fresh checkout — that's fine)
curl -sf http://localhost:8001/audit/log \
  | python3 -c "import sys,json; assert isinstance(json.load(sys.stdin), list)"

kill $SERVER_PID

echo "ALL SMOKE TESTS PASSED"
```

---

## Conflict resolution policy (summary)

| Scenario | Resolution |
|----------|-----------|
| `main.py` conflict (integrator only) | Keep all prior `include_router` calls; append new ones; never delete. |
| `contract.md` conflict | Block merge; escalate to repository owner. |
| Any test file conflict | Block merge; the owning lane must rebase and re-test. |
| Unowned file touched by a lane | Block merge; the lane agent must reset that file and re-commit. |

---

## Worktree setup commands (for A2 execution reference)

```bash
# Create worktrees (from repo root, on latest main)
git worktree add ../wt-lane-a -b feat/lane-a
git worktree add ../wt-lane-b -b feat/lane-b
git worktree add ../wt-lane-c -b feat/lane-c

# Clean up after all merges
git worktree remove ../wt-lane-a
git worktree remove ../wt-lane-b
git worktree remove ../wt-lane-c
```

---

## Definition of Done — planner verification checklist

Reviewer (or this planner run) confirms each item before marking A1 complete.

| # | Criterion | Result |
|---|-----------|--------|
| 1 | **Lane independence:** owned-file sets for A, B, C have zero overlap (only `main.py` / `contract.md` are shared forbidden files) | PASS — see `decomposition.md` overlap table |
| 2 | **Lane A prompt runnable in isolation:** goal, owned files, forbidden files, acceptance checklist, standalone `TestClient` pattern | PASS — `lanes/lane-a.prompt.md` |
| 3 | **Lane B prompt runnable in isolation:** same structure; no dependency on lane A files | PASS — `lanes/lane-b.prompt.md` |
| 4 | **Lane C prompt runnable in isolation:** same structure; `main.py` hook documented for integrator only | PASS — `lanes/lane-c.prompt.md` |
| 5 | **Shared constraints:** lint bootstrap, commit scopes, schema freeze, test gate, dep freeze | PASS — `constraints.md` |
| 6 | **Branch names:** `feat/lane-a`, `feat/lane-b`, `feat/lane-c` | PASS — §Branch names |
| 7 | **Merge order explicit:** A → B → C with rationale | PASS — §Merge order |
| 8 | **Conflict policy explicit:** `main.py` append-only; block on `contract.md` / unowned files | PASS — §Conflict resolution policy |
| 9 | **Per-merge verification:** pytest + `verify.sh` + spot-check curl after each merge | PASS — §Merge 1–3 |
| 10 | **Full-stack verification after all merges:** pytest, verify.sh, smoke curls | PASS — §Full verification plan |
| 11 | **Worktree commands** for A2 execution | PASS — §Worktree setup commands |

**Planner status:** PASS — all deliverables present and verified in
`VERIFICATION.log` (2026-06-17); lanes are parallel-safe with integrator-only
`main.py` wiring after each merge.
