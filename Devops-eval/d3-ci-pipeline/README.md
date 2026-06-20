# GitHub Actions CI — D3

## Trigger

Push or PR to `main`/`master`.

## Local run

```bash
./scripts/verify.sh
```

Or install [act](https://github.com/nektos/act) and run stages manually:

```bash
ruff check app tests
PYTHONPATH=. pytest tests/ -v
docker build -t devops-eval-app:local .
```

## Logs

- `act-run.log` — green pipeline output
- `broken-commit-run.log` — intentional lint failure demo

## Cache

`actions/setup-python` with `cache: pip` and Docker GHA cache in build-image job.
