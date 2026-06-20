# Ledger API (Node / Express)

A tiny in-memory transaction ledger with input validation and tests — the Node
counterpart of the FastAPI example.

## Endpoints

| Method | Path            | Description                          |
|--------|-----------------|--------------------------------------|
| POST   | `/transactions` | Create a transaction (validated)     |
| GET    | `/transactions` | List all transactions                |
| GET    | `/balance`      | Current balance (credits − debits)   |

Body: `{ "amount": <number > 0>, "type": "credit" | "debit", "description"?: string }`.
Invalid input returns HTTP `422`.

## Install

```bash
npm install
```

## Run

```bash
npm start            # listens on http://127.0.0.1:3000
```

Example:

```bash
curl -X POST localhost:3000/transactions -H 'content-type: application/json' \
  -d '{"amount": 100, "type": "credit"}'
curl localhost:3000/balance
```

## Test

```bash
npm test
```
