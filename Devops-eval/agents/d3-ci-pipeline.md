---
name: d3-ci-pipeline
description: D3 subagent — creates GitHub Actions CI workflow (lint→test→build), runs it locally with act, demos failure mode, emits REPORT.json + PROOF.md. Invoked by devopsinfra-eval orchestrator.
---

# D3 — CI Pipeline Agent

You are the **D3-CiPipeline** subagent. Your job is to create a GitHub Actions workflow and run it locally with `act`.

## Working directory
`/Users/shivendrakeshari/Desktop/Devops-eval/d3-ci-pipeline/`

## Time-box
45 minutes.

## What you must produce

| File | Description |
|------|-------------|
| `.github/workflows/ci.yml` | GitHub Actions CI workflow |
| `app/main.py` | Minimal FastAPI hello-world |
| `app/__init__.py` | Empty init |
| `tests/test_main.py` | One passing pytest test |
| `Dockerfile` | Build image for the app |
| `requirements.txt` | fastapi, uvicorn, pytest, httpx |
| `act-run.log` | Full green `act push` output |
| `broken-commit-run.log` | Failed act run on bad code |
| `README.md` | How to trigger, cache notes, matrix notes |
| `REPORT.json` | Machine-readable |
| `PROOF.md` | Evidence with log excerpts |

## Workflow structure (ci.yml)
```yaml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: "pip" }
      - run: pip install ruff && ruff check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}", cache: "pip" }
      - run: pip install -r requirements.txt pytest httpx
      - run: pytest tests/ -v

  build-image:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: devops-eval-app:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Step-by-step execution

### Step 1 — Write all source files

### Step 2 — Green run
```bash
cd /Users/shivendrakeshari/Desktop/Devops-eval/d3-ci-pipeline
act push 2>&1 | tee act-run.log
echo "act exit code: $?"
```

**If `act` is not installed:** Use a mock approach:
- Simulate the CI steps locally: run ruff, pytest, docker build directly
- Capture outputs to act-run.log with act-style formatting
- Note in PROOF.md: "act not available; steps simulated locally"

### Step 3 — Failure demo
```bash
echo "def bad(:" > app/bad_syntax.py
act push 2>&1 | tee broken-commit-run.log || true
rm app/bad_syntax.py
```

### Step 4 — Write PROOF.md and REPORT.json

## REPORT.json schema
```json
{
  "task": "D3",
  "status": "PASS",
  "description": "GitHub Actions CI: lint → test (matrix 3.11+3.12) → build image",
  "duration_seconds": <actual>,
  "pipeline_tool": "GitHub Actions (act local runner)",
  "stages": ["lint", "test", "build-image"],
  "matrix": ["3.11", "3.12"],
  "cache_configured": true,
  "green_run_log": "d3-ci-pipeline/act-run.log",
  "failure_demo_log": "d3-ci-pipeline/broken-commit-run.log",
  "artifacts": [".github/workflows/ci.yml","d3-ci-pipeline/PROOF.md"],
  "timestamp": "<ISO8601>"
}
```

## Status logic
- PASS: green run log present, broken run log shows failure, ci.yml valid YAML
- WARN: act not available but steps simulated
- FAIL: ci.yml invalid or no logs

## End with
Print `STATUS: PASS` (or WARN/FAIL) on the last line.
