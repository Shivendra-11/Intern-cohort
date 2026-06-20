# D3 — CI Pipeline (45m)

## Workflow: .github/workflows/ci.yml
Stages: **lint** (ruff) → **test** (pytest, matrix 3.11+3.12) → **build-image** (docker buildx)

## Local runner
Use `act` (https://github.com/nektos/act) to run locally:
```bash
act push --job lint
act push        # full pipeline
```

## Target app
Create a minimal Python app in d3-ci-pipeline/app/:
- `app/main.py`  (FastAPI hello-world)
- `tests/test_main.py`  (one passing test)
- `Dockerfile`
- `requirements.txt`

## Pipeline structure
```yaml
name: CI
on: [push, pull_request]
jobs:
  lint:      # ruff check .
  test:      # pytest (matrix: 3.11, 3.12)
    needs: lint
  build-image:  # docker buildx (no push)
    needs: test
```

## Failure demo
```bash
echo "def bad(:" > app/bad.py
act push 2>&1 | tee broken-commit-run.log
rm app/bad.py
```

## DoD
- act exits 0 for green run (captured in act-run.log)
- act exits non-zero for broken run (captured in broken-commit-run.log)
- Both logs present
- REPORT.json written
- PROOF.md contains log excerpts
