---
agent: A4
session_id: "20260617-074928"
status: pass
---

# A4 — Repository Modernization

**Target:** `a4-modernization/target-repo/`  
**Baseline:** `eb834b8`

## Findings summary

| ID | Title | Severity | Addressed |
|----|-------|----------|-----------|
| F1 | Legacy setup.py packaging | high | yes |
| F2 | Unpinned dependencies | medium | yes |
| F3 | Stale Python classifiers | low | yes |
| F4 | No ruff configuration | medium | no |
| F5 | Missing .gitignore | low | no |

### F1 — Legacy `setup.py` (selected)

- **Evidence:** `setup.py:1-12` — no `pyproject.toml`
- **Impact:** Non-reproducible installs
- **Action:** Migrate to PEP 621

## Priority matrix

| Finding | Value | Risk | Score | Selected |
|---------|-------|------|-------|----------|
| F1 | high | low | 92 | **yes** |
| F2 | high | low | 78 | no |
| F4 | medium | low | 65 | no |

> **Rationale:** F1 is highest value with lowest risk — packaging-only change.

## Implemented step

- **Branch:** `modernize/first-step`
- **Change:** Added `pyproject.toml` with `[project]` and `[build-system]`
- **Verification:** `pytest -q` → 5 passed

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "textkit"
version = "0.2.0"
requires-python = ">=3.10"
```

## Rollback notes

1. `git checkout main && git branch -D modernize/first-step`
2. Restore `setup.py` from baseline `eb834b8`
3. Remove `pyproject.toml`
4. Re-run `pytest` to confirm baseline

See `attachments/rollback.md` for full procedure.
