# A3 — Polyglot Mini-System (FastAPI + Node + Rust)

A fraud-score pipeline across three languages, wired by a file-queue (no broker):

```
UI (index.html) ──POST /transaction──▶ FastAPI (main.py)
        ▲                                   │ writes queue/incoming/
        │ GET /transaction/<id> (poll)      ▼
        │                            Node worker (worker/index.js)
        │                                   │ pipes JSON on stdin
        └──────────── score ◀───── Rust engine (fraud-engine/)
```

See [contract.md](contract.md) for the exact data contract and scoring weights.

## Prerequisites
- **Python 3.12** — on this machine: `/opt/homebrew/bin/python3.12`
  (the default `python3` is 3.9 and will not work).
- **Node 20+**, **Rust/Cargo** (1.78+).

## How to run (4 terminals / steps)

```bash
# 1. Backend deps (build the venv with python3.12, NOT the default python3)
cd a3-polyglot
/opt/homebrew/bin/python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# 2. Build the Rust engine (the worker invokes its binary)
cargo build --manifest-path fraud-engine/Cargo.toml

# 3. Start the API
uvicorn main:app --reload --port 8000        # terminal 1

# 4. Start the worker
node worker/index.js                          # terminal 2

# 5. Open the dashboard
open ui/index.html                            # terminal 3 (or open the file)
```

Submit a transaction in the UI: the 3 status steps light up as it flows
FastAPI → Node → Rust, the gauge shows the risk score (green/amber/red), and a
row is added to the history table. The **Run Tests** button calls `GET /run-tests`.

## Tests

```bash
# all three suites at once
bash ../shared/lib/verify.sh .

# or individually
.venv/bin/python -m pytest -q                              # FastAPI contract tests
npm test --prefix worker                                   # Node worker tests
cargo test --manifest-path fraud-engine/Cargo.toml         # Rust scoring tests
```

## Layout
```
a3-polyglot/
├── main.py              FastAPI ingest + status + run-tests + health (CORS *)
├── requirements.txt
├── contract.md          the cross-component data contract
├── tests/test_api.py    FastAPI TestClient + contract tests
├── worker/
│   ├── index.js         polling loop (zero deps)
│   ├── lib.js           testable worker core
│   ├── package.json     `npm test` = node --test
│   └── test/worker.test.js
├── fraud-engine/        Rust CLI: stdin JSON → stdout score JSON
│   ├── Cargo.toml
│   └── src/{lib.rs,main.rs}
├── queue/               file-queue (incoming/ status/ results/) — gitignored
└── ui/index.html        self-contained dashboard (Chart.js via CDN)
```

## Notes
- `queue/` holds runtime artifacts and is gitignored.
- CORS is set to `*` so the UI works when opened from `file://`.
- If the UI shows the red banner, FastAPI isn't running on port 8000; if scores
  never arrive, the Node worker or Rust binary isn't running/built.
