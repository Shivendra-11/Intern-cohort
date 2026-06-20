# A5 — Adversarial Verification Log

Commands executed on 2026-06-18 from repo root using the A3 polyglot venv
(FastAPI + pytest available).

---

## ISS-002 — Off-by-one pagination (reproduced)

```bash
cd a5-code-review/pr-under-review
PYTHONPATH=. ../../a3-polyglot/.venv/bin/python -m pytest \
  tests/test_pagination.py::test_page_boundary_off_by_one -v
```

**Output:**

```
tests/test_pagination.py::test_page_boundary_off_by_one FAILED

AssertionError: expected 3 items, got 4: [0, 1, 2, 3]
assert 4 == 3
```

**Conclusion:** Bug confirmed — `paginate(items, page=0, page_size=3)` returns 4 rows.

---

## ISS-001 — Unauthenticated export (reproduced)

```bash
PYTHONPATH=. ../../a3-polyglot/.venv/bin/python -m pytest \
  tests/test_pagination.py::test_export_has_no_auth_gate -v
```

**Output:**

```
tests/test_pagination.py::test_export_has_no_auth_gate PASSED
```

The test documents current behaviour: `GET /transactions/export.csv` returns **HTTP 200**
with no auth gate. In a secured API this would be a vulnerability.

**Manual check:**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.export import router
app = FastAPI(); app.include_router(router)
assert TestClient(app).get("/transactions/export.csv").status_code == 200
```

---

## ISS-003 — Threshold validator branch (partial)

```bash
PYTHONPATH=. ../../a3-polyglot/.venv/bin/python -m pytest \
  tests/test_pagination.py::test_threshold_invalid_order_raises -v
```

**Output:**

```
tests/test_pagination.py::test_threshold_invalid_order_raises PASSED
```

Validator raises on bad ordering; PR still lacks an HTTP-level 422 test in its own suite.

---

## Full suite (expected: 1 fail, 2 pass)

```bash
PYTHONPATH=. ../../a3-polyglot/.venv/bin/python -m pytest tests/test_pagination.py -v
```

**Output summary:** `1 failed, 2 passed` — failure is ISS-002 off-by-one test.
