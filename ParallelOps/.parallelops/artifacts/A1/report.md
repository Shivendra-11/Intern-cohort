---
agent: A1
session_id: "20260617-074928"
status: pass
---

# A1 — Multi-Worktree Parallel Plan

> Planning-only run. No branches or code were modified.

## Summary

Three independent lanes decompose **CSV export**, **threshold config**, and **audit log** for `a3-polyglot/`. Owned files do not overlap; `main.py` is integrator-only.

## Lane decomposition

| Lane | Branch | Worktree | Goal |
|------|--------|----------|------|
| lane-a | `feat/lane-a-export` | `wt-lane-a` | `GET /transactions/export.csv` |
| lane-b | `feat/lane-b-thresholds` | `wt-lane-b` | `GET/PUT /config/thresholds` |
| lane-c | `feat/lane-c-audit` | `wt-lane-c` | HIGH RISK audit log + `GET /audit/log` |

### Lane A — owned files

- `a3-polyglot/routers/export.py`
- `a3-polyglot/tests/test_export.py`

**Forbidden:** `main.py`, `routers/thresholds.py`

## Merge order

1. `lane-a` → `main`
2. `lane-b` → `main`
3. `lane-c` → `main`

```bash
# Post-merge verification (each step)
bash shared/lib/verify.sh a3-polyglot
```

## Risk plan

| ID | Category | Severity | Mitigation |
|----|----------|----------|------------|
| R1 | shared_hot_file | high | Integrator-only `main.py` wiring |
| R2 | schema_drift | medium | Sign-off on threshold JSON shape |
| R3 | test_gate | medium | `verify.sh` after each merge |

## Verification plan

- [x] 2–3 independent lanes with explicit file ownership
- [x] Zero owned-file overlap (`OVERLAP: none`)
- [x] Merge order + conflict policy documented
- [x] Per-lane and post-merge verify commands listed

## Architecture reference

![Parallel lane split — lanes converge at main.py integrator](attachments/lanes-diagram.svg)

*Diagram: optional attachment under `attachments/`.*
