# DevOps-Infra Eval

Six-task DevOps and infrastructure evaluation harness with an AI orchestrator agent and a React results dashboard.

## Live deployment

**Eval dashboard (reports):** [https://devopsinfra-dash.vercel.app/](https://devopsinfra-dash.vercel.app/)

**Services hub (all task UIs):** [https://devopsinfra-dash.vercel.app/hub](https://devopsinfra-dash.vercel.app/hub)

| Link | URL |
|------|-----|
| **Eval dashboard** (reports) | [devopsinfra-dash.vercel.app](https://devopsinfra-dash.vercel.app/) |
| **Services hub** (all task UIs) | [devopsinfra-dash.vercel.app/hub](https://devopsinfra-dash.vercel.app/hub) |

**Current score:** 6/6 PASS · 0 WARN · 0 FAIL · **~92/100**

Anyone can open these links without cloning the repo. After you run new eval tasks locally, redeploy with `./deploy.sh` to refresh the public reports.

---

## What this agent does

The **DevOps-Infra Eval** agent (`/devopsinfra-eval`) is an AI orchestrator that runs six standardized infrastructure tasks against this repository. You pick one or more tasks and a mode; the agent dispatches specialized subagents, builds deliverables, runs verification, and writes proof artifacts.

**Flow:**

1. You choose task(s) **D1–D6** and mode (`plan`, `build`, or `build+verify`).
2. The orchestrator dispatches the matching subagent for each task in order.
3. Each subagent produces `REPORT.json` and `PROOF.md` in its task folder.
4. The orchestrator updates `EVAL-REPORT.md` with pass/warn/fail scores.
5. The React dashboard reads those reports and shows status, logs, and links to live services.

**Modes**

| Mode | What happens |
|------|----------------|
| `plan` | Write `PLAN.md` only — no execution |
| `build` | Build all deliverables, skip verification |
| `build+verify` | Build + run all verification commands (recommended) |

**In Cursor or Claude Code**, start with:

```
/devopsinfra-eval
```

Or run a specific task directly:

```
/devopsinfra-eval --task D3 --mode build+verify
/devopsinfra-eval --task all --mode build+verify
```

---

## The six tasks (D1–D6)

| Task | Folder | What it builds |
|------|--------|----------------|
| **D1** | `d1-terraform/` | Terraform: S3 + Lambda + API Gateway (offline validate/plan) |
| **D2** | `d2-compose-stack/` | Docker Compose: FastAPI + Postgres + background worker + E2E tests |
| **D3** | `d3-ci-pipeline/` | GitHub Actions CI (lint → test → build) with local `act` demo |
| **D4** | `d4-kubernetes/` | Kubernetes manifests on a local `kind` cluster |
| **D5** | `d5-dev-env/` | Reproducible dev environment: `devcontainer.json` + `Makefile` bootstrap |
| **D6** | `d6-observability/` | Prometheus metrics, structured logs, Grafana dashboards |

Each task folder contains source code, verification scripts, `REPORT.json`, and `PROOF.md`.

---

## Setup

### Prerequisites

| Tool | Used by |
|------|---------|
| **Node.js 18+** | Dashboard, Vercel deploy |
| **Python 3.9+** | D2/D3/D6 APIs, tests |
| **Terraform ≥ 1.6** | D1 |
| **Docker + Docker Compose** | D2, D4, D6 (full verify) |
| **kind + kubectl** | D4 |
| **Homebrew** (macOS) | Optional: Grafana, Prometheus, cloudflared |

### 1. Clone and install

```bash
git clone https://github.com/Shivendra-11/DevopsInfra-eval.git
cd DevopsInfra-eval

./install-devopsinfra.sh
```

This installs agent definitions and the eval skill into `~/.claude/`, links task reports into the dashboard, and runs `npm install` for the UI.

### 2. Configure secrets (local only)

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
VERCEL_TOKEN=your-vercel-token   # only needed for ./deploy.sh
```

`.env` is gitignored. Never commit tokens.

### 3. Run the eval agent

In **Cursor** or **Claude Code** (after `install-devopsinfra.sh`):

```
/devopsinfra-eval
```

Follow the prompts to pick tasks and mode.

### 4. View results locally

**Dashboard only** (reports from `REPORT.json` files):

```bash
./serve-eval-dashboard.sh
# → http://localhost:5173
```

**All local service UIs** (D2/D3/D6 APIs, Prometheus, Grafana, dashboard):

```bash
./run-all-ui.sh
# → http://localhost:5173/hub
```

**Optional — temporary public link** (Cloudflare tunnel, while your machine is running):

```bash
./run-all-ui.sh --share
```

**Full Docker stack** (D2 + D4 kind + D6):

```bash
./run-all-ui-docker.sh
./run-all-ui.sh
```

Stop everything:

```bash
./stop-all-ui.sh
```

---

## Repository layout

```
Devops-eval/
├── agents/              # Subagent definitions (D1–D6) — installed to ~/.claude/agents/
├── skill/               # Orchestrator skill — installed to ~/.claude/skills/devopsinfra-eval/
├── dashboard/           # React eval dashboard (Vite + TypeScript)
├── d1-terraform/        # D1 — Terraform IaC
├── d2-compose-stack/    # D2 — FastAPI + Postgres + worker
├── d3-ci-pipeline/      # D3 — GitHub Actions CI
├── d4-kubernetes/       # D4 — K8s manifests + kind
├── d5-dev-env/          # D5 — devcontainer + Makefile
├── d6-observability/    # D6 — Prometheus + Grafana + metrics
├── shared/              # Shared utilities
├── scripts/             # Build and env helpers
├── deploy.sh            # Deploy dashboard to Vercel (permanent public URL)
├── run-all-ui.sh        # Start all local UIs
├── EVAL-REPORT.md       # Latest aggregated eval results (updated by agent)
└── DEVOPSINFRA-EVAL-PLAN.md  # Full build plan and spec
```

---

## Deploy to Vercel (update public link)

Public URL: **https://devopsinfra-dash.vercel.app/**

```bash
# Add VERCEL_TOKEN and VERCEL_INSECURE_TLS=1 to .env first
./deploy.sh
```

The permanent URL is printed and saved to `.devopsinfra/DEPLOY-LINK.txt` (local only, gitignored).

See [DEPLOY.md](./DEPLOY.md) for token setup and corporate VPN SSL workarounds.

---

## Latest eval results

See [EVAL-REPORT.md](./EVAL-REPORT.md) for the most recent run summary.

| Task | Status (last run) |
|------|-------------------|
| D1 Terraform | PASS |
| D2 Compose | PASS |
| D3 CI pipeline | PASS |
| D4 Kubernetes | PASS |
| D5 Dev environment | PASS |
| D6 Observability | PASS |

Each task includes `./scripts/verify.sh` for reproducible proof generation.

---

## Further reading

- [DEVOPSINFRA-EVAL-PLAN.md](./DEVOPSINFRA-EVAL-PLAN.md) — full task spec, acceptance criteria, dashboard design
- [DEPLOY.md](./DEPLOY.md) — Vercel deployment guide
- Per-task `README.md` and `PROOF.md` inside each `d*/` folder
