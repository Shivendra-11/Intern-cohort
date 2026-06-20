# A3 — Polyglot Mini-System (FastAPI + Node + Rust)  [150 min]

> Run via `/parallelops-eval` → select **A3** → dispatches `polyglot-builder`.
> **This task is fully built in the repo** — see the running instructions in `README.md`.

## Goal
A fraud-score system: FastAPI ingests transactions, a Node.js worker processes
them, a Rust CLI computes the risk score.

## Architecture (file-queue pipeline, zero external brokers)
```
UI ──POST /transaction──▶ FastAPI ──writes──▶ queue/incoming/<id>.json (queued)
                                                      │ polls
                              Node worker ◀───────────┘
                                  │ writes queue/status/<id>.json (node_picked_up)
                                  │ pipes txn JSON on stdin
                                  ▼
                              Rust fraud-engine ──score JSON──▶ Node
                                  │ writes queue/results/<id>.json (scored)
UI ◀──GET /transaction/<id>── FastAPI (merges results→status→incoming)
```

## Data contract
See `contract.md` (single source of truth). Verdict bands: 0–30 Low (green),
31–70 Medium (amber), 71–100 High (red).

## Components
- `main.py` — FastAPI: `POST /transaction`, `GET /transaction/{id}`,
  `GET /transactions`, `GET /run-tests`, `GET /health`; CORS `*`.
- `worker/index.js` — Node worker polling the queue and invoking the Rust binary.
- `fraud-engine/` — Rust CLI: stdin txn JSON → stdout `{score, verdict, factors}`;
  pure `score_transaction()` in `src/lib.rs` with unit tests.
- `ui/index.html` — self-contained dashboard (form, 3-step status log, Chart.js
  gauge, history table, Run Tests).
- `tests/test_api.py` — FastAPI TestClient + contract tests.

## Build order
1. Scaffold the 3 stacks from repo-builder templates, then specialize.
2. Rust scorer + tests → `cargo test`.
3. FastAPI ingest/status/run-tests/health + CORS → `pytest`.
4. Node worker + queue.
5. UI + README + contract.
6. End-to-end smoke (uvicorn + worker + submit).

## Tools
Python 3.12 (`/opt/homebrew/bin/python3.12`), Node 20, Rust/Cargo 1.96.

## Definition of done
`pip install` + `uvicorn` + `node worker/index.js` run; a UI submit lights all 3
steps and shows a band-correct gauge + history row; `pytest`, `npm test`,
`cargo test` pass; `GET /run-tests` aggregates a pass; `README.md` + `contract.md`
accurate.

## Time breakdown
scaffold 25m · Rust scorer + tests 25m · FastAPI 35m · Node worker 25m · UI 30m ·
integration + README 10m.

## Pitfalls
- Using `python3` (3.9) instead of `python3.12`.
- Missing CORS → UI fetch fails silently.
- Wrong Rust binary path in Node (`fraud-engine/target/debug/fraud-engine`).
- Committing `queue/` artifacts.
- UI polling before the worker is started.
