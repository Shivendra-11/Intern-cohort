# A5 — Adversarial Code Review

**PR under review:** `pr-under-review/`  
**Reviewer:** adversarial-reviewer  
**Date:** 2026-06-18  
**STATUS:** PASS

---

## Issue summary

| ID | Category | Severity | Blocking | Location | Verified |
|----|----------|----------|----------|----------|----------|
| ISS-001 | security | Critical | yes | `routers/export.py:16` | yes |
| ISS-002 | correctness | High | yes | `utils/pagination.py:8` | yes |
| ISS-003 | test | Medium | no | `routers/thresholds.py:14` | no |
| ISS-004 | perf | Medium | no | `audit/dedup.py:5` | no |
| ISS-005 | maintainability | Low | no | `services/accounts.py:5-10` | no |

**Totals:** 5 issues · 2 blocking · 2 adversarially verified

---

## ISS-001 — Missing auth on export route (Critical · Blocking)

**What's wrong:** `GET /transactions/export.csv` returns sensitive transaction data with no authentication or authorization check. Any caller receives CSV output.

**Fix:**

```python
from fastapi import Depends

@router.get("/transactions/export.csv")
async def export_csv(_: Admin = Depends(require_admin)):
    ...
```

**Verification:** `curl` or TestClient without credentials returns 200 today; should return 401/403 after fix.

---

## ISS-002 — Off-by-one pagination (High · Blocking)

**What's wrong:** `paginate()` uses `end = start + page_size + 1`, returning one extra row past the page boundary.

**Fix:**

```python
end = min(start + page_size, len(items))
return items[start:end]
```

**Verification:** `pytest tests/test_pagination.py::test_page_boundary_off_by_one` fails on current code (returns 4 items instead of 3).

---

## ISS-003 — Untested 422 branch on threshold validation (Medium · Non-blocking)

**What's wrong:** Invalid threshold ordering raises `ValueError` in the model validator, but the PR adds no test asserting HTTP 422 (or equivalent) for bad payloads.

**Fix:** Add `test_put_invalid_order_returns_422` covering `{low_max: 50, medium_max: 40, high_min: 70}`.

**Verification:** Run expanded threshold test module; confirm 422 case is covered.

---

## ISS-004 — O(n²) dedup in audit helper (Medium · Non-blocking)

**What's wrong:** `dedup_entries()` scans the entire `unique` list for every input row — quadratic time on large audit logs.

**Fix:** Track seen `txn_id` values in a `set` while preserving order in the output list.

**Verification:** Benchmark with 10k entries; compare median runtime before/after.

---

## ISS-005 — Inconsistent naming (`get_*` vs `fetch_*`) (Low · Non-blocking)

**What's wrong:** `services/accounts.py` mixes `get_user` and `fetch_account` for the same class of read operation.

**Fix:** Standardize on one prefix (e.g. `get_user`, `get_account`) across the module.

**Verification:** Grep for `fetch_` in services layer after rename; ensure call sites updated.

---

## Review checklist

- [x] Correctness pass
- [x] Security pass
- [x] Test coverage gaps noted
- [x] Performance smells flagged
- [x] ≥1 bug adversarially verified (ISS-001, ISS-002)
