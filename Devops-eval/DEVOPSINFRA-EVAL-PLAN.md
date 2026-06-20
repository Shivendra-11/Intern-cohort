# DevOps-Infra Eval — Complete Build Plan

> **Scope:** `/devopsinfra-eval` skill + 6 subagents (D1–D6) + unified React dashboard UI  
> **Mirror pattern:** follows `parallelops-eval` / `polyglot-builder` conventions exactly  
> **Working directory:** `/Users/shivendrakeshari/Desktop/Devops-eval/`

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Directory Layout](#2-directory-layout)
3. [File Creation Order](#3-file-creation-order)
4. [Orchestrator Skill — `/devopsinfra-eval`](#4-orchestrator-skill)
5. [Subagent D1 — Terraform Plan](#5-subagent-d1--terraform-plan)
6. [Subagent D2 — Docker Compose Stack](#6-subagent-d2--docker-compose-stack)
7. [Subagent D3 — CI Pipeline](#7-subagent-d3--ci-pipeline)
8. [Subagent D4 — Kubernetes Manifests](#8-subagent-d4--kubernetes-manifests)
9. [Subagent D5 — Reproducible Dev Environment](#9-subagent-d5--reproducible-dev-environment)
10. [Subagent D6 — Observability Bolt-On](#10-subagent-d6--observability-bolt-on)
11. [Dashboard UI — Architecture & Components](#11-dashboard-ui)
12. [Dashboard UI — Per-Subagent Panels (D1–D6)](#12-dashboard-per-panel-design)
13. [Dashboard UI — Build Plan (React + Vite)](#13-dashboard-build-plan)
14. [Shared Utilities](#14-shared-utilities)
15. [Install Script](#15-install-script)
16. [Execution Sequence](#16-execution-sequence)

---

## 1. System Architecture Overview

```
User types /devopsinfra-eval
         │
         ▼
  SKILL.md (orchestrator)
  ├── AskQuestion  → which task(s)? D1 / D2 / D3 / D4 / D5 / D6 / all
  ├── AskQuestion  → which mode?  Plan / Build / Build+Verify
  └── dispatch subagent(s) via Agent tool
         │
         ├── d1-terraform      → ~/.claude/agents/d1-terraform.md
         ├── d2-compose-stack  → ~/.claude/agents/d2-compose-stack.md
         ├── d3-ci-pipeline    → ~/.claude/agents/d3-ci-pipeline.md
         ├── d4-kubernetes     → ~/.claude/agents/d4-kubernetes.md
         ├── d5-dev-env        → ~/.claude/agents/d5-dev-env.md
         └── d6-observability  → ~/.claude/agents/d6-observability.md
                    │
                    ▼
         Each writes deliverables into its folder
         plus a machine-readable  REPORT.json
                    │
                    ▼
         Orchestrator writes EVAL-REPORT.md
                    │
                    ▼
         Dashboard server reads REPORT.json files
         → React Vite SPA  http://localhost:5173
```

### Key design decisions (mirrors ParallelOps)

| Concern | Decision |
|---------|----------|
| Subagent format | One `.md` per agent under `~/.claude/agents/` |
| Skill entry point | `~/.claude/skills/devopsinfra-eval/SKILL.md` |
| Working root | `/Users/shivendrakeshari/Desktop/Devops-eval/` |
| Proof format | Every subagent emits `REPORT.json` + `PROOF.md` |
| Dashboard tech | React 18 + Vite + Tailwind CSS (no backend needed, reads local JSON) |
| Dashboard server | `dashboard/serve.py` (Python http.server serving dist/) |
| Time boxes | D1 60m · D2 90m · D3 45m · D4 60m · D5 45m · D6 60m |

---

## 2. Directory Layout

```
/Users/shivendrakeshari/Desktop/Devops-eval/
├── DEVOPSINFRA-EVAL-PLAN.md          ← this file
├── EVAL-REPORT.md                    ← written by orchestrator after each run
├── install-devopsinfra.sh            ← one-shot setup script
├── serve-eval-dashboard.sh           ← start dashboard
│
├── shared/
│   └── lib/
│       ├── verify.sh                 ← shared test runner helper
│       └── timer.sh                  ← time-box tracking helper
│
├── d1-terraform/
│   ├── PLAN.md                       ← task spec (written once, never regenerated)
│   ├── REPORT.json                   ← machine-readable result (written by D1 agent)
│   ├── PROOF.md                      ← human-readable evidence
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   ├── backend.tf
│   └── README.md
│
├── d2-compose-stack/
│   ├── PLAN.md
│   ├── REPORT.json
│   ├── PROOF.md
│   ├── docker-compose.yml
│   ├── api/
│   │   ├── Dockerfile
│   │   └── app/
│   ├── worker/
│   │   ├── Dockerfile
│   │   └── src/
│   ├── db/
│   │   └── seed.sql
│   ├── tests/
│   │   └── e2e_test.sh
│   └── README.md
│
├── d3-ci-pipeline/
│   ├── PLAN.md
│   ├── REPORT.json
│   ├── PROOF.md
│   ├── .github/
│   │   └── workflows/
│   │       └── ci.yml
│   ├── act-run.log                   ← local act runner output
│   ├── broken-commit-run.log         ← failure mode demo
│   └── README.md
│
├── d4-kubernetes/
│   ├── PLAN.md
│   ├── REPORT.json
│   ├── PROOF.md
│   ├── manifests/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── ingress.yaml
│   ├── apply.log                     ← kubectl apply output
│   ├── curl-proof.log                ← curl port-forward response
│   └── README.md
│
├── d5-dev-env/
│   ├── PLAN.md
│   ├── REPORT.json
│   ├── PROOF.md
│   ├── devcontainer.json             ← OR Makefile / flake.nix
│   ├── .tool-versions                ← asdf/mise version pins
│   ├── bootstrap.log                 ← full command output
│   ├── test-run.log                  ← passing test output
│   └── README.md
│
├── d6-observability/
│   ├── PLAN.md
│   ├── REPORT.json
│   ├── PROOF.md
│   ├── service/
│   │   ├── app.py                    ← instrumented service
│   │   └── metrics.py
│   ├── docker-compose.obs.yml        ← Prometheus + Grafana stack
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   ├── provisioning/
│   │   │   ├── datasources/ds.yaml
│   │   │   └── dashboards/dashboard.json
│   │   └── dashboards/
│   │       └── devops-eval.json      ← provisioned dashboard panel
│   ├── load.sh                       ← traffic generator
│   ├── dashboard-screenshot.png      ← proof screenshot
│   └── README.md
│
└── dashboard/                        ← React Vite SPA
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── index.html
    ├── serve.py                      ← python3 -m http.server wrapper
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── types.ts                  ← shared TypeScript types
        ├── data/
        │   └── loadReports.ts        ← reads all REPORT.json files
        ├── components/
        │   ├── Header.tsx
        │   ├── ScoreCard.tsx         ← overall PASS/WARN/FAIL summary
        │   ├── TaskGrid.tsx          ← 2×3 grid of task cards
        │   ├── TaskCard.tsx          ← individual D1–D6 card
        │   ├── StatusBadge.tsx       ← PASS / WARN / FAIL badge
        │   ├── EvidencePanel.tsx     ← expandable proof output
        │   └── panels/
        │       ├── D1TerraformPanel.tsx
        │       ├── D2ComposePanel.tsx
        │       ├── D3CiPanel.tsx
        │       ├── D4KubernetesPanel.tsx
        │       ├── D5DevEnvPanel.tsx
        │       └── D6ObsPanel.tsx
        └── pages/
            ├── DashboardPage.tsx     ← main view
            └── DetailPage.tsx        ← per-task drill-down
```

---

## 3. File Creation Order

Build in this exact order to avoid forward dependencies:

```
Phase 0 — Scaffold
  1.  install-devopsinfra.sh
  2.  shared/lib/verify.sh
  3.  shared/lib/timer.sh

Phase 1 — PLAN.md files (static, written once)
  4.  d1-terraform/PLAN.md
  5.  d2-compose-stack/PLAN.md
  6.  d3-ci-pipeline/PLAN.md
  7.  d4-kubernetes/PLAN.md
  8.  d5-dev-env/PLAN.md
  9.  d6-observability/PLAN.md

Phase 2 — Agent definition files
  10. ~/.claude/agents/d1-terraform.md
  11. ~/.claude/agents/d2-compose-stack.md
  12. ~/.claude/agents/d3-ci-pipeline.md
  13. ~/.claude/agents/d4-kubernetes.md
  14. ~/.claude/agents/d5-dev-env.md
  15. ~/.claude/agents/d6-observability.md

Phase 3 — Orchestrator skill
  16. ~/.claude/skills/devopsinfra-eval/SKILL.md

Phase 4 — Dashboard scaffold
  17. dashboard/package.json
  18. dashboard/vite.config.ts
  19. dashboard/tailwind.config.ts
  20. dashboard/index.html
  21. dashboard/src/types.ts
  22. dashboard/src/data/loadReports.ts
  23. dashboard/src/components/*.tsx  (8 shared components)
  24. dashboard/src/components/panels/*.tsx  (6 panel components)
  25. dashboard/src/pages/*.tsx  (2 pages)
  26. dashboard/src/main.tsx
  27. dashboard/src/App.tsx
  28. dashboard/serve.py
  29. serve-eval-dashboard.sh
```

---

## 4. Orchestrator Skill

**File:** `~/.claude/skills/devopsinfra-eval/SKILL.md`

### What it does

Mirrors `parallelops-eval/SKILL.md`. Entry point when user types `/devopsinfra-eval`.

### Behavior flow

```
Step 0  Parse inline flags  --task D1|D2|...|all  --mode plan|build|build+verify
Step 1  AskQuestion → which task(s)?  (multi-select D1–D6 or all)
Step 2  AskQuestion → which mode?
Step 3  Write .devopsinfra/eval_selection.json
Step 4  For each selected task dispatch the matching subagent via Agent tool
Step 5  Collect REPORT.json from each folder
Step 6  Write EVAL-REPORT.md  (scorecard)
Step 7  Offer dashboard URL:  http://localhost:5173
```

### Dispatch table

| Task | Folder | Agent name | Time-box |
|------|--------|-----------|----------|
| D1 | `d1-terraform/` | `d1-terraform` | 60m |
| D2 | `d2-compose-stack/` | `d2-compose-stack` | 90m |
| D3 | `d3-ci-pipeline/` | `d3-ci-pipeline` | 45m |
| D4 | `d4-kubernetes/` | `d4-kubernetes` | 60m |
| D5 | `d5-dev-env/` | `d5-dev-env` | 45m |
| D6 | `d6-observability/` | `d6-observability` | 60m |

### SKILL.md content skeleton

```markdown
---
name: devopsinfra-eval
description: DevOps-Infra Eval orchestrator — asks which task D1–D6 to run,
             dispatches the matching subagent, and updates EVAL-REPORT.md.
argument-hint: "[--task D1|D2|D3|D4|D5|D6|all] [--mode plan|build|build+verify]"
---

# /devopsinfra-eval — DevOps-Infra Eval orchestrator

You are **DevOpsInfra-Eval** — the single entry point for all six DevOps/Infra eval tasks (D1–D6).

[full content described in section below]
```

### EVAL-REPORT.md format

```markdown
# DevOps-Infra Eval Report — <timestamp>

| Task | Description | Mode | Status | Time | Key Artifacts |
|------|-------------|------|--------|------|---------------|
| D1   | Terraform plan | Build+Verify | ✅ PASS | 48m | d1-terraform/PROOF.md |
| D2   | Compose stack  | Build+Verify | ✅ PASS | 82m | d2-compose-stack/PROOF.md |
...

## Dashboard
http://localhost:5173
```

---

## 5. Subagent D1 — Terraform Plan

**File:** `~/.claude/agents/d1-terraform.md`  
**Task folder:** `d1-terraform/`  
**Time-box:** 60 minutes

### What it must deliver

| Deliverable | Description |
|-------------|-------------|
| `main.tf` | S3 bucket + Lambda + API Gateway (or GCS + Cloud Run) |
| `variables.tf` | All input vars with defaults |
| `outputs.tf` | Useful outputs (API URL, bucket ARN, etc.) |
| `provider.tf` | AWS or Google provider pinned to version |
| `backend.tf` | Local backend for offline validation |
| `terraform validate` | Must exit 0 — output captured in PROOF.md |
| `terraform plan` | Must produce clean plan — output captured in PROOF.md |
| `README.md` | apply and destroy commands, pre-requisites |
| `REPORT.json` | Machine-readable result for dashboard |
| `PROOF.md` | Full terminal output |

### Agent operating principles

```
1. Use AWS provider with localstack OR google provider with local mocks when
   real credentials are absent. Prefer local/mock backend so plan runs offline.
2. Pin provider version exactly (e.g., hashicorp/aws ~> 5.0).
3. Run: terraform init -backend=false && terraform validate
4. Run: terraform plan -var-file=dev.tfvars (or -var flags for defaults)
   Capture full output. A non-zero exit code = FAIL.
5. Write REPORT.json with keys: status, validate_exit_code, plan_exit_code,
   resource_count, duration_seconds, artifacts[].
6. End with STATUS: PASS|WARN|FAIL.
```

### REPORT.json schema (D1)

```json
{
  "task": "D1",
  "status": "PASS",
  "description": "Terraform plan for S3 + Lambda + API Gateway",
  "duration_seconds": 2847,
  "validate_exit_code": 0,
  "plan_exit_code": 0,
  "resource_count": 7,
  "resources": ["aws_s3_bucket.main", "aws_lambda_function.handler", ...],
  "artifacts": [
    "d1-terraform/main.tf",
    "d1-terraform/PROOF.md"
  ],
  "proof_excerpt": "Plan: 7 to add, 0 to change, 0 to destroy.",
  "timestamp": "2026-06-17T10:00:00Z"
}
```

### d1-terraform/PLAN.md content

```markdown
# D1 — Terraform Plan (60m)

## Goal
Write Terraform for: S3 bucket + Lambda (Python 3.12) + API Gateway (HTTP API).
Must pass `terraform validate` and produce a clean `terraform plan`.

## Provider choice
AWS provider ≥ 5.0 with local backend (no real credentials needed for validate/plan).

## Resource list
- aws_s3_bucket (versioning enabled, no public access)
- aws_s3_bucket_versioning
- aws_iam_role + aws_iam_role_policy_attachment (Lambda execution role)
- aws_lambda_function (runtime python3.12, handler index.handler)
- aws_apigatewayv2_api (HTTP API)
- aws_apigatewayv2_integration
- aws_apigatewayv2_route (GET /hello)

## Verification commands
terraform init -backend=false
terraform validate
terraform plan -var="environment=dev" -out=tfplan.binary
terraform show -no-color tfplan.binary > plan-output.txt

## DoD
validate exits 0, plan exits 0, plan shows ≥ 5 resources to add, README has
apply/destroy commands, REPORT.json written.
```

---

## 6. Subagent D2 — Docker Compose Stack

**File:** `~/.claude/agents/d2-compose-stack.md`  
**Task folder:** `d2-compose-stack/`  
**Time-box:** 90 minutes

### What it must deliver

| Deliverable | Description |
|-------------|-------------|
| `docker-compose.yml` | api + db (Postgres) + worker services |
| `api/Dockerfile` | FastAPI or Express app |
| `worker/Dockerfile` | Background job processor |
| `db/seed.sql` | Fixture data seeded on first start |
| `tests/e2e_test.sh` | One-command test runner (curl-based or pytest) |
| `tests/e2e_test.log` | Full green test output captured |
| `logs/cross-service.log` | Evidence services talked to each other |
| `README.md` | Up, test, teardown, clean re-up commands |
| `REPORT.json` | Machine-readable |
| `PROOF.md` | Evidence |

### Stack design

```
┌─────────────────────────────────────────┐
│  docker-compose.yml                     │
│                                         │
│  api (FastAPI :8000)                    │
│    └── depends_on: db                   │
│  worker (Python polling)                │
│    └── depends_on: db, api              │
│  db (postgres:16-alpine)                │
│    └── healthcheck: pg_isready          │
└─────────────────────────────────────────┘
```

### Service interaction proof

The e2e test must:
1. `POST /jobs` to API → returns `{job_id}`
2. Worker picks up job → updates DB status to `processed`
3. `GET /jobs/{id}` → status is `processed`
4. `docker-compose logs worker` shows the job ID

### REPORT.json schema (D2)

```json
{
  "task": "D2",
  "status": "PASS",
  "description": "docker-compose API + Postgres + worker with e2e tests",
  "duration_seconds": 5200,
  "services": ["api", "db", "worker"],
  "tests_total": 5,
  "tests_passed": 5,
  "tests_failed": 0,
  "cross_service_log_lines": 12,
  "teardown_command": "docker-compose down -v",
  "clean_reup_command": "docker-compose down -v && docker-compose up -d --build",
  "artifacts": ["d2-compose-stack/docker-compose.yml", "d2-compose-stack/PROOF.md"],
  "timestamp": "2026-06-17T10:00:00Z"
}
```

### d2-compose-stack/PLAN.md content

```markdown
# D2 — Docker Compose Stack + E2E Tests (90m)

## Stack
- api: FastAPI (Python 3.12) on port 8000
  - POST /jobs  → creates job record in DB, returns {job_id, status: "pending"}
  - GET /jobs/{id} → returns job with current status
  - GET /health
- worker: Python script that polls DB every 2s, picks pending jobs,
  marks them processed, logs "processed job <id>"
- db: postgres:16-alpine, port 5432
  - seed.sql creates table `jobs(id serial, payload jsonb, status text, created_at timestamptz)`

## Test plan (tests/e2e_test.sh)
1. docker-compose up -d --build && wait-for-it localhost:8000 -t 30
2. curl POST /jobs → capture job_id
3. sleep 5  (worker picks up)
4. curl GET /jobs/{job_id} → assert status == "processed"
5. docker-compose logs worker | grep "processed job ${job_id}"  → cross-service proof

## Teardown
docker-compose down -v

## DoD
All 5 test assertions pass, cross-service log line captured, teardown is clean,
REPORT.json written.
```

---

## 7. Subagent D3 — CI Pipeline

**File:** `~/.claude/agents/d3-ci-pipeline.md`  
**Task folder:** `d3-ci-pipeline/`  
**Time-box:** 45 minutes

### What it must deliver

| Deliverable | Description |
|-------------|-------------|
| `.github/workflows/ci.yml` | GitHub Actions workflow |
| `act-run.log` | Local `act` run output (green) |
| `broken-commit-run.log` | Failed `act` run on deliberately broken code |
| `README.md` | How to trigger, cache notes, matrix notes |
| `REPORT.json` | Machine-readable |
| `PROOF.md` | Evidence with log excerpts |

### Workflow stages

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
      - run: pip install -r requirements.txt pytest
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

### Failure mode demo

Create `bad-code.py` with a syntax error, run `act push` — capture the lint failure.

### REPORT.json schema (D3)

```json
{
  "task": "D3",
  "status": "PASS",
  "description": "GitHub Actions CI: lint → test (matrix 3.11+3.12) → build image",
  "duration_seconds": 1800,
  "pipeline_tool": "GitHub Actions (act local runner)",
  "stages": ["lint", "test", "build-image"],
  "matrix": ["3.11", "3.12"],
  "cache_configured": true,
  "green_run_log": "d3-ci-pipeline/act-run.log",
  "failure_demo_log": "d3-ci-pipeline/broken-commit-run.log",
  "artifacts": [".github/workflows/ci.yml", "d3-ci-pipeline/PROOF.md"],
  "timestamp": "2026-06-17T10:00:00Z"
}
```

### d3-ci-pipeline/PLAN.md content

```markdown
# D3 — CI Pipeline (45m)

## Workflow: .github/workflows/ci.yml
stages: lint (ruff) → test (pytest, matrix 3.11+3.12) → build-image (docker buildx)

## Local runner
Use `act` (https://github.com/nektos/act) to run locally:
  act push --job lint
  act push        # full pipeline

## Target app
Create a minimal Python app in d3-ci-pipeline/app/:
  app/main.py  (FastAPI hello-world)
  tests/test_main.py  (one passing test)
  Dockerfile
  requirements.txt

## Failure demo
  echo "def bad(:" > app/bad.py
  act push 2>&1 | tee broken-commit-run.log
  git rm app/bad.py

## DoD
act exits 0 for green run, exits non-zero for broken run, both logs captured,
REPORT.json written.
```

---

## 8. Subagent D4 — Kubernetes Manifests

**File:** `~/.claude/agents/d4-kubernetes.md`  
**Task folder:** `d4-kubernetes/`  
**Time-box:** 60 minutes

### What it must deliver

| Deliverable | Description |
|-------------|-------------|
| `manifests/deployment.yaml` | Deployment (2 replicas, resource limits) |
| `manifests/service.yaml` | ClusterIP service |
| `manifests/configmap.yaml` | App configuration |
| `manifests/ingress.yaml` | Ingress (optional, kind-nginx) |
| `apply.log` | Full `kubectl apply` output |
| `curl-proof.log` | curl via port-forward showing 200 OK |
| `dry-run.log` | `kubectl apply --dry-run=client` output |
| `README.md` | kind cluster up/down, apply, verify, destroy |
| `REPORT.json` | Machine-readable |
| `PROOF.md` | Evidence |

### Manifest design

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-eval-app
  namespace: devops-eval
spec:
  replicas: 2
  selector:
    matchLabels: { app: devops-eval-app }
  template:
    spec:
      containers:
        - name: app
          image: nginx:alpine          # swap for real image
          ports: [{ containerPort: 80 }]
          envFrom: [{ configMapRef: { name: app-config } }]
          resources:
            requests: { cpu: "50m", memory: "64Mi" }
            limits:   { cpu: "200m", memory: "128Mi" }
          readinessProbe:
            httpGet: { path: /, port: 80 }
```

### Verification sequence

```bash
# 1. Create kind cluster
kind create cluster --name devops-eval

# 2. Dry-run validate
kubectl apply -f manifests/ --dry-run=client 2>&1 | tee dry-run.log

# 3. Apply
kubectl create namespace devops-eval
kubectl apply -f manifests/ 2>&1 | tee apply.log

# 4. Wait for rollout
kubectl rollout status deployment/devops-eval-app -n devops-eval

# 5. Curl proof
kubectl port-forward svc/devops-eval-svc 8080:80 -n devops-eval &
sleep 2 && curl -s http://localhost:8080/ | tee curl-proof.log

# 6. Destroy
kind delete cluster --name devops-eval
```

### REPORT.json schema (D4)

```json
{
  "task": "D4",
  "status": "PASS",
  "description": "Kubernetes manifests on kind cluster",
  "duration_seconds": 3200,
  "cluster_tool": "kind",
  "namespace": "devops-eval",
  "manifest_files": ["deployment.yaml", "service.yaml", "configmap.yaml", "ingress.yaml"],
  "dry_run_exit_code": 0,
  "apply_exit_code": 0,
  "replicas_ready": 2,
  "curl_status_code": 200,
  "curl_response_excerpt": "Welcome to nginx!",
  "artifacts": ["d4-kubernetes/manifests/", "d4-kubernetes/PROOF.md"],
  "timestamp": "2026-06-17T10:00:00Z"
}
```

---

## 9. Subagent D5 — Reproducible Dev Environment

**File:** `~/.claude/agents/d5-dev-env.md`  
**Task folder:** `d5-dev-env/`  
**Time-box:** 45 minutes

### What it must deliver

| Deliverable | Description |
|-------------|-------------|
| `devcontainer.json` | VS Code Dev Container definition |
| `.tool-versions` | asdf/mise version pins (Python, Node, etc.) |
| `Makefile` | `make bootstrap` single command |
| `bootstrap.log` | Full output of bootstrap on clean machine |
| `test-run.log` | `make test` passing output |
| `implicit-deps.md` | What was previously implicit and is now explicit |
| `README.md` | The single command, what it does |
| `REPORT.json` | Machine-readable |
| `PROOF.md` | Evidence |

### Bootstrap approach (devcontainer.json + Makefile)

```json
{
  "name": "devops-eval",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/devcontainers/features/node:1": { "version": "20" },
    "ghcr.io/devcontainers/features/terraform:1": { "version": "latest" },
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "postCreateCommand": "make bootstrap",
  "forwardPorts": [8000, 5432, 5173],
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "hashicorp.terraform"]
    }
  }
}
```

```makefile
# Makefile
bootstrap:
	pip install -r requirements.txt
	npm install --prefix dashboard
	terraform -chdir=d1-terraform init -backend=false
	@echo "Bootstrap complete"

test:
	pytest d2-compose-stack/tests/ -q
	@echo "Tests passed"
```

### implicit-deps.md content skeleton

```markdown
# Previously implicit dependencies — now explicit

| Was implicit | Now explicit | Where pinned |
|---|---|---|
| Python 3.12 | Required by devcontainer image | devcontainer.json |
| Node v20 | Required by dashboard | devcontainer.json features + .tool-versions |
| Terraform ≥ 1.6 | Required for d1-terraform | devcontainer.json features |
| POSTGRES_PASSWORD env var | Must be set for d2 tests | .env.example |
| docker daemon | Must be running for d2/d3/d4 | devcontainer docker-in-docker feature |
```

### REPORT.json schema (D5)

```json
{
  "task": "D5",
  "status": "PASS",
  "description": "Reproducible dev environment via devcontainer.json + Makefile",
  "duration_seconds": 1900,
  "bootstrap_command": "make bootstrap",
  "bootstrap_exit_code": 0,
  "test_command": "make test",
  "test_exit_code": 0,
  "implicit_deps_documented": 5,
  "artifacts": ["d5-dev-env/devcontainer.json", "d5-dev-env/Makefile", "d5-dev-env/PROOF.md"],
  "timestamp": "2026-06-17T10:00:00Z"
}
```

---

## 10. Subagent D6 — Observability Bolt-On

**File:** `~/.claude/agents/d6-observability.md`  
**Task folder:** `d6-observability/`  
**Time-box:** 60 minutes

### What it must deliver

| Deliverable | Description |
|-------------|-------------|
| `service/app.py` | Instrumented FastAPI app (structured JSON logs + /metrics) |
| `service/metrics.py` | Prometheus counter/histogram definitions |
| `docker-compose.obs.yml` | Prometheus + Grafana compose file |
| `prometheus/prometheus.yml` | Scrape config pointing at service |
| `grafana/provisioning/datasources/ds.yaml` | Auto-provisioned Prometheus datasource |
| `grafana/dashboards/devops-eval.json` | Pre-provisioned dashboard JSON |
| `load.sh` | Traffic generator (50 req/s for 30s via curl loop or hey) |
| `dashboard-screenshot.png` | PNG of Grafana panel with live data |
| `README.md` | Run order, URLs |
| `REPORT.json` | Machine-readable |
| `PROOF.md` | Evidence |

### Instrumentation design

```python
# service/metrics.py
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)
```

```python
# service/app.py key additions
import structlog, time, json
log = structlog.get_logger()

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(duration)
    log.info("request", method=request.method, path=str(request.url.path),
             status=response.status_code, duration_ms=round(duration*1000, 2))
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Compose stack

```yaml
# docker-compose.obs.yml
services:
  service:
    build: ./service
    ports: ["8000:8000"]
  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports: ["9090:9090"]
  grafana:
    image: grafana/grafana:10.4.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    ports: ["3000:3000"]
    depends_on: [prometheus]
```

### Grafana dashboard panel (single working panel)

The provisioned dashboard must show:
- Panel: **"Requests per second"** — `rate(http_requests_total[1m])`
- Panel: **"p95 Latency"** — `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))`

### REPORT.json schema (D6)

```json
{
  "task": "D6",
  "status": "PASS",
  "description": "Observability bolt-on: structured logs + /metrics + Prometheus + Grafana",
  "duration_seconds": 3100,
  "metrics_endpoint": "http://localhost:8000/metrics",
  "prometheus_url": "http://localhost:9090",
  "grafana_url": "http://localhost:3000",
  "dashboard_panels": ["Requests per second", "p95 Latency"],
  "load_script": "d6-observability/load.sh",
  "screenshot": "d6-observability/dashboard-screenshot.png",
  "log_format": "JSON structured (structlog)",
  "artifacts": ["d6-observability/service/app.py", "d6-observability/PROOF.md"],
  "timestamp": "2026-06-17T10:00:00Z"
}
```

---

## 11. Dashboard UI — Architecture & Components

### Tech stack

| Choice | Reason |
|--------|--------|
| React 18 + TypeScript | Type-safe, fast to build |
| Vite 5 | Zero-config dev server, fast builds |
| Tailwind CSS 3 | Utility-first, no design system needed |
| React Router v6 | Dashboard page + per-task detail page |
| No backend | Reads REPORT.json files directly via fetch() from /public/ symlink |
| Recharts | Simple charts for latency/req metrics (D6 panel) |

### Data loading strategy

```typescript
// src/data/loadReports.ts
const TASKS = ['D1','D2','D3','D4','D5','D6'] as const

export async function loadAllReports(): Promise<TaskReport[]> {
  return Promise.all(
    TASKS.map(async (task) => {
      const folder = `d${task[1]}-${FOLDER_NAMES[task]}`
      try {
        const res = await fetch(`/reports/${folder}/REPORT.json`)
        if (!res.ok) return { task, status: 'NOT_RUN' }
        return await res.json()
      } catch {
        return { task, status: 'NOT_RUN' }
      }
    })
  )
}
```

The Vite dev server is configured to proxy `/reports/` → `../` (the task folders) so the dashboard reads live REPORT.json files without a backend.

### TypeScript types

```typescript
// src/types.ts
export type TaskStatus = 'PASS' | 'WARN' | 'FAIL' | 'NOT_RUN' | 'IN_PROGRESS'

export interface BaseReport {
  task: string
  status: TaskStatus
  description: string
  duration_seconds: number
  artifacts: string[]
  timestamp: string
}

export interface D1Report extends BaseReport {
  validate_exit_code: number
  plan_exit_code: number
  resource_count: number
  resources: string[]
  proof_excerpt: string
}

export interface D2Report extends BaseReport {
  services: string[]
  tests_total: number
  tests_passed: number
  tests_failed: number
  cross_service_log_lines: number
  teardown_command: string
}

export interface D3Report extends BaseReport {
  pipeline_tool: string
  stages: string[]
  matrix: string[]
  cache_configured: boolean
  green_run_log: string
  failure_demo_log: string
}

export interface D4Report extends BaseReport {
  cluster_tool: string
  namespace: string
  dry_run_exit_code: number
  apply_exit_code: number
  replicas_ready: number
  curl_status_code: number
  curl_response_excerpt: string
}

export interface D5Report extends BaseReport {
  bootstrap_command: string
  bootstrap_exit_code: number
  test_command: string
  test_exit_code: number
  implicit_deps_documented: number
}

export interface D6Report extends BaseReport {
  metrics_endpoint: string
  prometheus_url: string
  grafana_url: string
  dashboard_panels: string[]
  load_script: string
  screenshot: string
  log_format: string
}
```

---

## 12. Dashboard Per-Panel Design

### Overall layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  DevOps-Infra Eval Dashboard                          [Run All] [?]  │
│  Last run: 2026-06-17 10:32 UTC                                      │
├──────────────┬──────────────┬──────────────┬──────────────────────  │
│  Score Card  │              │              │                          │
│  5/6 PASS    │  Total time  │  Tasks run   │  [Start Dashboard ↗]    │
│  1 WARN      │  5h 32m      │  6           │                          │
├──────────────┴──────────────┴──────────────┴──────────────────────  │
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ D1 Terraform   │  │ D2 Compose     │  │ D3 CI Pipeline │         │
│  │ ✅ PASS  48m   │  │ ✅ PASS  82m   │  │ ✅ PASS  38m   │         │
│  │ 7 resources    │  │ 5/5 tests pass │  │ 2 stages green │         │
│  │ [View →]       │  │ [View →]       │  │ [View →]       │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ D4 Kubernetes  │  │ D5 Dev Env     │  │ D6 Observ.     │         │
│  │ ✅ PASS  55m   │  │ ⚠️ WARN  41m   │  │ ✅ PASS  58m   │         │
│  │ 2/2 pods ready │  │ 4/5 deps expl. │  │ /metrics live  │         │
│  │ [View →]       │  │ [View →]       │  │ [View →]       │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### D1 Detail Panel

```
┌─────────────────────────────────────────────────────────┐
│  D1 — Terraform Plan                      ✅ PASS        │
├─────────────────────────────────────────────────────────┤
│  Resources planned (7):                                  │
│  ● aws_s3_bucket.main                                    │
│  ● aws_lambda_function.handler                           │
│  ● aws_apigatewayv2_api.main          ...               │
│                                                          │
│  Validation output:                                      │
│  ╔══════════════════════════════════════╗               │
│  ║ Success! The configuration is valid. ║               │
│  ╚══════════════════════════════════════╝               │
│                                                          │
│  Plan summary:                                           │
│  Plan: 7 to add, 0 to change, 0 to destroy.             │
│                                                          │
│  Artifacts: main.tf · variables.tf · outputs.tf          │
└─────────────────────────────────────────────────────────┘
```

### D2 Detail Panel

```
┌─────────────────────────────────────────────────────────┐
│  D2 — Compose Stack                       ✅ PASS        │
├─────────────────────────────────────────────────────────┤
│  Services: api · db · worker                             │
│                                                          │
│  Test Results:  ████████████████████  5/5 passed         │
│  ✅ POST /jobs returns 201                               │
│  ✅ Worker picks up job within 5s                        │
│  ✅ GET /jobs/{id} shows status=processed                │
│  ✅ Cross-service log line found                         │
│  ✅ Clean teardown with docker-compose down -v           │
│                                                          │
│  Cross-service proof:                                    │
│  worker_1  | processed job 42                           │
└─────────────────────────────────────────────────────────┘
```

### D3 Detail Panel

```
┌─────────────────────────────────────────────────────────┐
│  D3 — CI Pipeline                         ✅ PASS        │
├─────────────────────────────────────────────────────────┤
│  Pipeline: lint → test (3.11, 3.12) → build-image        │
│                                                          │
│  ✅ lint         0m 12s                                  │
│  ✅ test/3.11    1m 45s                                  │
│  ✅ test/3.12    1m 42s                                  │
│  ✅ build-image  2m 18s                                  │
│                                                          │
│  Failure demo:                                           │
│  ❌ lint FAILED — ruff found syntax error in bad.py     │
│  Exit code: 1 ✓ (expected failure)                      │
│                                                          │
│  Cache: ✅ pip cache configured (actions/cache)          │
└─────────────────────────────────────────────────────────┘
```

### D4 Detail Panel

```
┌─────────────────────────────────────────────────────────┐
│  D4 — Kubernetes                          ✅ PASS        │
├─────────────────────────────────────────────────────────┤
│  Cluster: kind v0.22 (devops-eval)                       │
│  Namespace: devops-eval                                  │
│                                                          │
│  Dry-run: ✅ 4 resources validated                       │
│  Apply:   ✅ deployment.apps/devops-eval-app created      │
│  Rollout: ✅ 2/2 pods ready                              │
│                                                          │
│  Curl proof:                                             │
│  $ curl http://localhost:8080/                           │
│  HTTP/1.1 200 OK                                         │
│  <!DOCTYPE html><h1>Welcome to nginx!</h1>               │
│                                                          │
│  Manifests: deployment · service · configmap · ingress   │
└─────────────────────────────────────────────────────────┘
```

### D5 Detail Panel

```
┌─────────────────────────────────────────────────────────┐
│  D5 — Dev Environment                     ⚠️ WARN        │
├─────────────────────────────────────────────────────────┤
│  Bootstrap command:  make bootstrap                      │
│  Exit code: 0 ✅                                         │
│                                                          │
│  Test command:  make test                                │
│  Exit code: 0 ✅                                         │
│                                                          │
│  Previously implicit (now explicit):                     │
│  ● Python 3.12         → devcontainer.json              │
│  ● Node v20            → .tool-versions                 │
│  ● Terraform ≥ 1.6     → devcontainer.json              │
│  ● POSTGRES_PASSWORD   → .env.example                   │
│  ⚠ docker-in-docker   → manual step still needed        │
│                                                          │
│  4/5 deps documented (1 still manual)                   │
└─────────────────────────────────────────────────────────┘
```

### D6 Detail Panel

```
┌─────────────────────────────────────────────────────────┐
│  D6 — Observability                       ✅ PASS        │
├─────────────────────────────────────────────────────────┤
│  Metrics endpoint: http://localhost:8000/metrics  ✅      │
│  Prometheus:       http://localhost:9090           ✅      │
│  Grafana:          http://localhost:3000           ✅      │
│                                                          │
│  Dashboard panels:                                       │
│  ● Requests per second   [live chart placeholder]        │
│  ● p95 Latency ms        [live chart placeholder]        │
│                                                          │
│  Load test: 50 req/s × 30s = 1,500 total requests       │
│  Log format: JSON structured (structlog)                 │
│                                                          │
│  [View Screenshot →]  [Open Grafana →]                  │
└─────────────────────────────────────────────────────────┘
```

---

## 13. Dashboard Build Plan (React + Vite)

### Step-by-step build sequence

#### Step 1 — Initialize project

```bash
cd /Users/shivendrakeshari/Desktop/Devops-eval
mkdir dashboard && cd dashboard
npm create vite@latest . -- --template react-ts
npm install tailwindcss postcss autoprefixer recharts react-router-dom
npx tailwindcss init -p
```

#### Step 2 — Configure Vite proxy

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/reports': {
        target: 'http://localhost:5173',
        rewrite: (p) => p,
      }
    }
  },
  publicDir: 'public',
  resolve: { alias: { '@': path.resolve(__dirname, './src') } }
})
```

Reports are symlinked: `dashboard/public/reports → ../` so `fetch('/reports/d1-terraform/REPORT.json')` reads the live file.

#### Step 3 — App routing

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import DetailPage from './pages/DetailPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/task/:taskId" element={<DetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}
```

#### Step 4 — DashboardPage

```tsx
// src/pages/DashboardPage.tsx
import { useEffect, useState } from 'react'
import { loadAllReports } from '../data/loadReports'
import ScoreCard from '../components/ScoreCard'
import TaskGrid from '../components/TaskGrid'
import Header from '../components/Header'

export default function DashboardPage() {
  const [reports, setReports] = useState([])
  useEffect(() => { loadAllReports().then(setReports) }, [])

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <Header />
      <ScoreCard reports={reports} />
      <TaskGrid reports={reports} />
    </div>
  )
}
```

#### Step 5 — Component specs

**Header.tsx**
- Title: "DevOps-Infra Eval"
- Subtitle: last-run timestamp (from most recent REPORT.json)
- "Run All" button: opens terminal hint (no-op in UI, shows command)
- Dark navy background, monospace font

**ScoreCard.tsx**
- 3 stat chips: `N/6 PASS`, `N WARN`, `N FAIL`
- Green/amber/red color per count
- Total duration (sum of all duration_seconds)
- "Open Dashboard" button → `window.open('http://localhost:5173')`

**TaskCard.tsx**
```tsx
interface Props { report: BaseReport | null; taskId: string }
// Shows: task ID badge, description, status badge, duration, 2-line metric summary
// onClick → navigate to /task/D1
// Border color: green=PASS, amber=WARN, red=FAIL, gray=NOT_RUN
```

**StatusBadge.tsx**
```tsx
// PASS → green pill "✅ PASS"
// WARN → amber pill "⚠️ WARN"
// FAIL → red pill "❌ FAIL"
// NOT_RUN → gray pill "— NOT RUN"
// IN_PROGRESS → blue animated pill "⏳ RUNNING"
```

**EvidencePanel.tsx**
```tsx
// Expandable <details> element with <pre> code block
// Shows raw terminal output (validate/plan/curl/test logs)
// Syntax highlight key lines: PASS=green, FAIL=red, warning=amber
```

**TaskGrid.tsx**
```tsx
// 2-column grid on mobile, 3-column on ≥ lg
// Maps D1–D6 → TaskCard
// Handles NOT_RUN state gracefully (gray dimmed card)
```

#### Step 6 — Per-task panel components

Each lives in `src/components/panels/DxPanel.tsx`.  
They receive the typed report and render task-specific fields.

**D1TerraformPanel.tsx**
- Resource list (badge pills)
- Validate + plan exit codes (green ✅ / red ❌)
- `proof_excerpt` in `<EvidencePanel>`

**D2ComposePanel.tsx**
- Service pills (api / db / worker)
- Test progress bar: `tests_passed / tests_total`
- Cross-service log excerpt

**D3CiPanel.tsx**
- Stage pipeline diagram (horizontal chevrons)
- Matrix badges (3.11 / 3.12)
- Cache indicator
- Failure demo section (collapsible)

**D4KubernetesPanel.tsx**
- Replica readiness gauge (2/2)
- Dry-run + apply exit codes
- curl response code + body excerpt

**D5DevEnvPanel.tsx**
- Bootstrap command + exit code
- Test command + exit code
- Implicit deps table (was implicit → now explicit → where pinned)

**D6ObsPanel.tsx**
- Endpoint URL chips (metrics, prometheus, grafana)
- Dashboard panels list
- Screenshot (if PNG exists, renders `<img>`)
- External link buttons to Prometheus / Grafana

#### Step 7 — DetailPage

```
/task/D1 → renders full D1TerraformPanel + EvidencePanel with full PROOF.md text
/task/D2 → renders full D2ComposePanel + log tab switcher
...
```

Uses `useParams` to get `taskId`, `useEffect` to fetch that report, then renders the matching panel.

#### Step 8 — Serve script

```bash
#!/usr/bin/env bash
# serve-eval-dashboard.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DASH="$ROOT/dashboard"

# Symlink reports dir into public/
ln -sfn "$ROOT" "$DASH/public/reports"

cd "$DASH"
if [ ! -d node_modules ]; then
  npm install
fi

echo ""
echo "  DevOps-Infra Eval Dashboard"
echo "  http://localhost:5173"
echo ""
npm run dev
```
---
## 14. Shared Utilities

### shared/lib/verify.sh

```bash
#!/usr/bin/env bash
# Generic verification helper used by subagents
# Usage: ./shared/lib/verify.sh <task> <command> <expected_exit>
TASK=$1; CMD=$2; EXPECTED=${3:-0}
echo "=== verify [$TASK] ==="
eval "$CMD"
EXIT=$?
if [ "$EXIT" -eq "$EXPECTED" ]; then
  echo "VERIFY PASS: $TASK (exit $EXIT)"
else
  echo "VERIFY FAIL: $TASK expected exit $EXPECTED got $EXIT"
  exit 1
fi
```

### shared/lib/timer.sh

```bash
#!/usr/bin/env bash
# Usage: source timer.sh; START_TIMER; ... ; ELAPSED=$(STOP_TIMER)
START_TIMER() { _TIMER_START=$(date +%s); }
STOP_TIMER()  { echo $(( $(date +%s) - _TIMER_START )); }
```

---

## 15. Install Script

**File:** `install-devopsinfra.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing DevOps-Infra Eval..."

# 1. Create task folders + PLAN.md files
for d in d1-terraform d2-compose-stack d3-ci-pipeline d4-kubernetes d5-dev-env d6-observability; do
  mkdir -p "$ROOT/$d"
done
mkdir -p "$ROOT/shared/lib"

# 2. Install agent definition files
AGENTS_DIR="$CLAUDE_DIR/agents"
mkdir -p "$AGENTS_DIR"
cp "$ROOT/agents/"*.md "$AGENTS_DIR/" 2>/dev/null || true

# 3. Install skill
SKILL_DIR="$CLAUDE_DIR/skills/devopsinfra-eval"
mkdir -p "$SKILL_DIR"
cp "$ROOT/skill/SKILL.md" "$SKILL_DIR/SKILL.md"

# 4. Install dashboard deps
if [ -d "$ROOT/dashboard" ]; then
  cd "$ROOT/dashboard"
  npm install
  ln -sfn "$ROOT" "$ROOT/dashboard/public/reports"
fi

echo ""
echo "DevOps-Infra Eval installed."
echo "  Type /devopsinfra-eval in Claude Code to start."
echo "  Run ./serve-eval-dashboard.sh to open the dashboard."
```

---

## 16. Execution Sequence

When a user runs `/devopsinfra-eval --task all --mode build+verify`:

```
1. Orchestrator reads eval_selection.json (or creates it)
2. Sequential dispatch (each task folder is independent):
   D1 → d1-terraform agent   → writes REPORT.json + PROOF.md
   D2 → d2-compose-stack agent → writes REPORT.json + PROOF.md
   D3 → d3-ci-pipeline agent  → writes REPORT.json + PROOF.md
   D4 → d4-kubernetes agent   → writes REPORT.json + PROOF.md
   D5 → d5-dev-env agent      → writes REPORT.json + PROOF.md
   D6 → d6-observability agent → writes REPORT.json + PROOF.md
3. Orchestrator aggregates → writes EVAL-REPORT.md
4. Orchestrator prints:
   DevOps-Infra Eval complete
   - D1: PASS — d1-terraform/PROOF.md
   - D2: PASS — d2-compose-stack/PROOF.md
   ...
   Dashboard: http://localhost:5173  (run ./serve-eval-dashboard.sh)
```

### Independent vs sequential

D1, D3, D5 can run in parallel (no Docker daemon needed for D1/D5/D3 validate).  
D2, D4, D6 need Docker — run sequentially to avoid port conflicts.  
Safe default: sequential D1 → D2 → D3 → D4 → D5 → D6.

### Status definitions

| Status | Meaning |
|--------|---------|
| PASS | All verifications exited 0, all deliverables present |
| WARN | Deliverables present, one non-critical verification skipped |
| FAIL | Critical verification failed or deliverable missing |
| NOT_RUN | Agent not dispatched yet |

---

## Summary Checklist

### Agents to create (6 files in `~/.claude/agents/`)

- [ ] `d1-terraform.md`
- [ ] `d2-compose-stack.md`
- [ ] `d3-ci-pipeline.md`
- [ ] `d4-kubernetes.md`
- [ ] `d5-dev-env.md`
- [ ] `d6-observability.md`

### Skill to create (1 file in `~/.claude/skills/devopsinfra-eval/`)

- [ ] `SKILL.md`

### PLAN.md files to create (6 files in task folders)

- [ ] `d1-terraform/PLAN.md`
- [ ] `d2-compose-stack/PLAN.md`
- [ ] `d3-ci-pipeline/PLAN.md`
- [ ] `d4-kubernetes/PLAN.md`
- [ ] `d5-dev-env/PLAN.md`
- [ ] `d6-observability/PLAN.md`

### Dashboard files to create

- [ ] `dashboard/package.json`
- [ ] `dashboard/vite.config.ts`
- [ ] `dashboard/tailwind.config.ts`
- [ ] `dashboard/index.html`
- [ ] `dashboard/src/types.ts`
- [ ] `dashboard/src/data/loadReports.ts`
- [ ] `dashboard/src/components/Header.tsx`
- [ ] `dashboard/src/components/ScoreCard.tsx`
- [ ] `dashboard/src/components/TaskGrid.tsx`
- [ ] `dashboard/src/components/TaskCard.tsx`
- [ ] `dashboard/src/components/StatusBadge.tsx`
- [ ] `dashboard/src/components/EvidencePanel.tsx`
- [ ] `dashboard/src/components/panels/D1TerraformPanel.tsx`
- [ ] `dashboard/src/components/panels/D2ComposePanel.tsx`
- [ ] `dashboard/src/components/panels/D3CiPanel.tsx`
- [ ] `dashboard/src/components/panels/D4KubernetesPanel.tsx`
- [ ] `dashboard/src/components/panels/D5DevEnvPanel.tsx`
- [ ] `dashboard/src/components/panels/D6ObsPanel.tsx`
- [ ] `dashboard/src/pages/DashboardPage.tsx`
- [ ] `dashboard/src/pages/DetailPage.tsx`
- [ ] `dashboard/src/main.tsx`
- [ ] `dashboard/src/App.tsx`
- [ ] `dashboard/serve.py`
- [ ] `serve-eval-dashboard.sh`

### Shared utilities

- [ ] `shared/lib/verify.sh`
- [ ] `shared/lib/timer.sh`
- [ ] `install-devopsinfra.sh`
- [ ] `EVAL-REPORT.md` (template stub)
