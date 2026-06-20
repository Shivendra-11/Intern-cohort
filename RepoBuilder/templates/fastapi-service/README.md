# Ledger Service (FastAPI)

A tiny in-memory transaction ledger with input validation and tests.

## Endpoints

| Method | Path            | Description                          |
|--------|-----------------|--------------------------------------|
| POST   | `/transactions` | Create a transaction (validated)     |
| GET    | `/transactions` | List all transactions                |
| GET    | `/balance`      | Current balance (credits − debits)   |

A transaction is `{ "amount": <float > 0>, "type": "credit" | "debit", "description"?: string }`.
Invalid input returns HTTP `422` (enforced by Pydantic).

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
# then visit http://127.0.0.1:8000/docs for interactive Swagger UI
```

Example:

```bash
curl -X POST localhost:8000/transactions -H 'content-type: application/json' \
  -d '{"amount": 100, "type": "credit"}'
curl localhost:8000/balance
```

## Test

```bash
pytest -q
```
