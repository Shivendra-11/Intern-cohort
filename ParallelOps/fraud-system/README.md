# Fraud-scoring mini-system

A small polyglot pipeline that scores transactions for fraud risk. **Python (FastAPI)** accepts transactions and writes them to a **file queue**; a **Node.js worker** drains the queue and pipes each job to a **Rust scoring engine** via stdin/stdout. Results land back on disk and are read by the API. No database, no message broker, no UI — only `curl` for demos.

```
  curl POST                file queue              stdin/stdout
 ---------->  FastAPI  --> incoming/  -->  Node worker  -->  Rust engine
                ^                                              |
                |         results/  <-------------------------+
                +-------- GET /transaction/{id}
```

## Prerequisites

- **Python 3.12** at `/opt/homebrew/bin/python3.12` (do not use system `python3` 3.9)
- **Node.js 20.x**
- **Rust / Cargo** (recent stable)

## Run order

```bash
# 0. Build the Rust engine
cd fraud-system/fraud-engine && cargo build && cd ..

# 1. Python env + deps
/opt/homebrew/bin/python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# 2. Start the API (terminal 1)
uvicorn main:app --reload --port 8000

# 3. Start the worker (terminal 2)
node worker/index.js          # add --once to drain and exit

# 4. Submit a transaction (terminal 3)
curl -s -X POST localhost:8000/transaction \
  -H 'Content-Type: application/json' \
  -d '{"amount":9000,"merchant":"Acme","location":"unknown","card_type":"prepaid","timestamp":"2026-06-17T03:00:00Z"}'
# → {"txn_id":"...","stage":"queued"}

# 5. Poll for the score
curl -s localhost:8000/transaction/<txn_id>
```

## Data contract

See [contract.md](./contract.md) for the full JSON schema across all three hops.

## Running tests

```bash
# Rust unit tests
cargo test --manifest-path fraud-engine/Cargo.toml

# Node ↔ Rust contract
npm test --prefix worker

# Python API + end-to-end integration
pytest -v

# Aggregated (also available at GET /run-tests when API is running)
curl -s localhost:8000/run-tests
```

## `.gitignore`

Ignores `.venv/`, `node_modules/`, `fraud-engine/target/`, queue artifacts under `queue/incoming/*`, `queue/status/*`, `queue/results/*`, and `__pycache__/`.
