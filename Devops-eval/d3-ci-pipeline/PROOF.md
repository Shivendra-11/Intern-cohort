# D3 — CI Pipeline — Proof

## Green run

See `act-run.log`:
- ruff lint: All checks passed
- pytest 3.11 + 3.12: 2 passed each
- docker build: image sha256:a6f35b9ae9b2...
- act dry-run: lint, test (matrix), build-image jobs succeeded

## Failure demo

See `broken-commit-run.log` — ruff catches `SyntaxError` in bad.py.

## Workflow

`.github/workflows/ci.yml`: lint → test (matrix 3.11+3.12) → build-image with GHA cache.

## Verify

```bash
./scripts/verify.sh
```
