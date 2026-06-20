---
agent: A3
session_id: "20260617-074928"
status: pass
---

# A3 — Polyglot Fraud-Score Mini-System

## Stack overview

| Component | Language | Path | Tests |
|-----------|----------|------|-------|
| FastAPI | Python | `a3-polyglot/main.py` | 9 |
| Node Worker | JavaScript | `a3-polyglot/worker/` | 4 |
| Rust Engine | Rust | `a3-polyglot/fraud-engine/` | 6 |

## Data flow

```
UI → FastAPI → queue/incoming/ → Node Worker → Rust (stdin) → queue/results/ → FastAPI
```

## FastAPI contract

```json
{
  "amount": 4200.50,
  "merchant": "Acme Corp",
  "location": "NYC",
  "card_type": "credit",
  "timestamp": "2026-06-17T10:30:00Z"
}
```

Response `202`:

```json
{ "txn_id": "<32-hex>", "stage": "queued" }
```

## Node worker

- Polls `queue/incoming/*.json`
- Pipes JSON to Rust binary on **stdin**
- Writes `queue/results/<txn_id>.json`

> The file-queue under `queue/` is the message bus — no broker required.

## Rust engine output

```json
{
  "score": 92,
  "verdict": "High Risk",
  "factors": ["amount $4200.50 (+42)", "..."]
}
```

## Integration tests

1. `cargo test` — 6 passed
2. `pytest a3-polyglot/tests/` — 9 passed
3. `npm test` (worker) — 4 passed
4. `bash shared/lib/verify.sh a3-polyglot` — **VERIFY: PASS**

## Blockquote — design constraint

> Components communicate only through the documented queue contract. No direct HTTP calls between worker and engine.

## Dashboard UI

Self-contained UI at `a3-polyglot/ui/index.html` (Chart.js via CDN).

![Pipeline architecture](attachments/architecture.png)
