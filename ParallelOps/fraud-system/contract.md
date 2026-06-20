# Fraud-scoring data contract

Single source of truth for the Python → Node → Rust pipeline.

## 1. Client → FastAPI — `POST /transaction`

Request body:

```json
{
  "amount": 4200.50,
  "merchant": "Acme Corp",
  "location": "NYC",
  "card_type": "credit",
  "timestamp": "2026-06-17T10:30:00Z"
}
```

| Field | Type | Rules |
|-------|------|-------|
| `amount` | float | > 0, required |
| `merchant` | string | non-empty, required |
| `location` | string | non-empty, required |
| `card_type` | string | one of `credit`, `debit`, `prepaid`, required |
| `timestamp` | string | ISO-8601, required |

Response:

```json
{ "txn_id": "<uuid4>", "stage": "queued" }
```

FastAPI writes `queue/incoming/<txn_id>.json` with the original payload plus `txn_id` and `stage: "queued"`.

## 2. FastAPI → Node worker (file queue)

Worker reads `queue/incoming/<txn_id>.json`.

## 3. Node worker → Rust engine (stdin/stdout)

Worker pipes transaction JSON to the Rust binary on **stdin**. Rust prints to **stdout**:

```json
{ "score": 73, "verdict": "High Risk", "factors": ["large_amount", "odd_hour"] }
```

| Field | Type | Rules |
|-------|------|-------|
| `score` | integer | 0–100 |
| `verdict` | string | `Low Risk` (0–30), `Medium Risk` (31–70), `High Risk` (71–100) |
| `factors` | string[] | human-readable risk drivers |

## Status progression

| File | Content |
|------|---------|
| `queue/status/<txn_id>.json` | `{"txn_id":"...","stage":"node_picked_up", ...}` |
| `queue/results/<txn_id>.json` | `{"txn_id":"...","stage":"scored","score":73,"verdict":"High Risk","factors":[...], ...original fields}` |
| (deleted) | `queue/incoming/<txn_id>.json` removed after scoring |

## 4. Status read — `GET /transaction/<txn_id>`

Merge order: **results → status → incoming** (most advanced stage wins).

Examples:

- Only incoming → `stage: "queued"`
- Status exists → `stage: "node_picked_up"`
- Result exists → `stage: "scored"` with `score`, `verdict`, `factors`

## Scoring logic (Rust)

Deterministic heuristic (see `fraud-engine/src/lib.rs`):

- Amount: +1 point per $100, capped at 50; factor `large_amount` when amount ≥ 3000
- Unknown location: +20; factor `unknown_location`
- Prepaid card: +15; factor `prepaid_card`
- Odd hour (before 06:00 or at/after 23:00): +15; factor `odd_hour`
- Score clamped to 0–100
