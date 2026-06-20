# A3 Data Contract

The single source of truth shared by the three components. The file-queue under
`queue/` is the message bus (no broker/DB needed).

## 1. UI → FastAPI: `POST /transaction`
Request body (JSON):
```json
{
  "amount": 4200.50,
  "merchant": "Acme Corp",
  "location": "NYC",
  "card_type": "credit",
  "timestamp": "2026-06-17T10:30:00Z"
}
```
Validation (Pydantic, HTTP 422 on failure): `amount > 0`; `merchant`/`location`
non-empty; `card_type ∈ {credit, debit, prepaid}`; `timestamp` ISO-8601 string.

Response `202`:
```json
{ "txn_id": "<32-hex>", "stage": "queued" }
```

## 2. FastAPI → queue
Writes `queue/incoming/<txn_id>.json`:
```json
{ "txn_id": "...", "stage": "queued", "enqueued_at": "...", "amount": ..., "merchant": "...",
  "location": "...", "card_type": "...", "timestamp": "..." }
```

## 3. Node worker → queue + Rust
- On pickup writes `queue/status/<txn_id>.json` with `"stage": "node_picked_up"`.
- Pipes the transaction JSON to the Rust binary on **stdin**.
- Writes `queue/results/<txn_id>.json` (original fields + result, `"stage": "scored"`).
- Removes the incoming file. On engine failure writes `"stage": "error"` instead.

## 4. Rust `fraud-engine`: stdin → stdout
Input (stdin): the transaction JSON. Output (stdout):
```json
{ "score": 92, "verdict": "High Risk", "factors": ["amount $4200.50 (+42)", "..."] }
```
Non-zero exit (no panic) on invalid input.

## 5. UI ← FastAPI: `GET /transaction/<txn_id>`
Merges `results → status → incoming`:
```json
{ "txn_id": "...", "stage": "queued|node_picked_up|scored",
  "score": 92, "verdict": "High Risk", "factors": [...],
  "amount": ..., "merchant": "...", "location": "...", "card_type": "...", "timestamp": "..." }
```
`score`/`verdict`/`factors` are `null` until `stage == "scored"`. `404` if unknown.

## Other endpoints
- `GET /transactions` — all scored transactions, newest first (history table).
- `GET /transactions/export.csv` — CSV download of scored transactions.
- `GET /config/thresholds` / `PUT /config/thresholds` — runtime verdict band config.
- `GET /audit/log` — persisted HIGH RISK audit entries (score ≥ 71).
- `GET /run-tests` — runs pytest + npm test + cargo test; `{ "passed": bool, "output": "..." }`.
- `GET /health` — `{ "status": "ok" }` (UI uses it for the unreachable banner).

## Verdict bands
| Score | Verdict | Color |
|-------|---------|-------|
| 0–30 | Low Risk | green |
| 31–70 | Medium Risk | amber |
| 71–100 | High Risk | red |

## Scoring weights (Rust)
`amount`: +1 per $100 (cap 50) · unknown/empty `location`: +20 · `prepaid`: +15 ·
odd-hour (`hour < 6` or `hour >= 23`): +15 · clamped to 0–100.
