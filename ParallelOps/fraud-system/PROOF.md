# PROOF.md — A3 Polyglot Fraud-Scoring Mini-System

Real command output from this build session. Repo: `fraud-system/` under ParallelOps.

---

## 1. Tool versions

```
$ /opt/homebrew/bin/python3.12 --version
Python 3.12.13

$ node --version
v20.20.2

$ cargo --version
cargo 1.96.0 (30a34c682 2026-05-25)

$ git --version
git version 2.50.1 (Apple Git-155)
```

---

## 2. `cargo test` (Rust unit tests)

```
$ cd fraud-engine && cargo build && cargo test

running 4 tests
test tests::boundary_medium ... ok
test tests::high_risk_large_unknown_prepaid_odd_hour ... ok
test tests::score_is_clamped ... ok
test tests::low_risk_small_normal ... ok

test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

---

## 3. Piped stdin smoke (high-risk)

```
$ echo '{"amount":9000,"location":"unknown","card_type":"prepaid","timestamp":"2026-06-17T03:00:00Z"}' | ./target/debug/fraud-engine
{"score":100,"verdict":"High Risk","factors":["large_amount","unknown_location","prepaid_card","odd_hour"]}
```

---

## 4. `npm test --prefix worker` (Node ↔ Rust contract)

```
$ npm test --prefix worker

> fraud-worker@1.0.0 test
> node --test test/worker.test.js

ok 1 - rust binary exists
ok 2 - node to rust contract — high risk txn

# tests 2
# pass 2
# fail 0
```

---

## 5. `pytest -v` (API + integration)

```
$ pytest -v

tests/test_api.py::test_health PASSED
tests/test_api.py::test_post_enqueues_and_returns_id PASSED
tests/test_api.py::test_validation_rejects_bad_input[bad0] PASSED
tests/test_api.py::test_validation_rejects_bad_input[bad1] PASSED
tests/test_api.py::test_validation_rejects_bad_input[bad2] PASSED
tests/test_api.py::test_get_unknown_id_404 PASSED
tests/test_api.py::test_end_to_end_integration PASSED

========================= 7 passed, 1 warning in 0.84s =========================
```

---

## 6. End-to-end transcript (uvicorn + curl + worker --once)

```
$ uvicorn main:app --port 8000
INFO:     Uvicorn running on http://127.0.0.1:8000

$ curl -s -X POST localhost:8000/transaction \
  -H 'Content-Type: application/json' \
  -d '{"amount":9000,"merchant":"Acme","location":"unknown","card_type":"prepaid","timestamp":"2026-06-17T03:00:00Z"}'
{"txn_id":"197116d3-e0ef-4203-b85a-e1af12d58c19","stage":"queued"}

$ node worker/index.js --once
[worker] queue   .../fraud-system/queue/incoming
[worker] engine  .../fraud-engine/target/debug/fraud-engine
[worker] 197116d3-e0ef-4203-b85a-e1af12d58c19 -> score=100 (High Risk)

$ curl -s localhost:8000/transaction/197116d3-e0ef-4203-b85a-e1af12d58c19
{"txn_id":"197116d3-e0ef-4203-b85a-e1af12d58c19","stage":"scored","score":100,"verdict":"High Risk","factors":["large_amount","unknown_location","prepaid_card","odd_hour"],"amount":9000.0,"merchant":"Acme","location":"unknown","card_type":"prepaid","timestamp":"2026-06-17T03:00:00Z"}
```

---

## 7. `GET /run-tests` (aggregated)

```
$ curl -s localhost:8000/run-tests
passed: True

### pytest: PASS
7 passed, 1 warning in 0.40s

### npm test (worker): PASS
# pass 2

### cargo test: PASS
running 4 tests
...
```

Full JSON response had `"passed": true` with combined stdout/stderr from all three suites.

---

## Acceptance criteria

| Criterion | Status | Proof |
|-----------|--------|-------|
| FastAPI validates input (422 on bad data) | ✅ | `pytest -v` — `test_validation_rejects_bad_input` |
| Node worker processes queue + calls Rust | ✅ | `npm test` + `test_end_to_end_integration` |
| Rust lib + CLI score 0–100 with verdict/factors | ✅ | `cargo test` + stdin smoke |
| Data contract in `contract.md` | ✅ | file on disk |
| Rust unit tests + Python e2e integration | ✅ | all green above |
| README with run order | ✅ | `README.md` |
| No UI built | ✅ | no HTML/CSS/dashboard files |
