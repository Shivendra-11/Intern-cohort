# Intern Cohort — AI Agent Evaluation Suite

A combined portfolio of four AI agent evaluation frameworks built during the intern cohort. Each project ships a React dashboard, standardized eval tasks, proof artifacts, and a live Vercel deployment.

---

## Combined link (share this)

**One URL for all four dashboards:** [https://ai-agent-eval-suite.vercel.app](https://ai-agent-eval-suite.vercel.app)

This hub page links to all four live eval dashboards. No login or local setup required.

## Verify everything (one command)

```bash
make install   # first time only — editable-installs the Python packages
make test      # runs all 182 tests (Python + Node + Rust); Node/Rust skip gracefully if absent
```

Independently reproduced results — 172 Python + 4 Node + 6 Rust tests, 0 failures —
are recorded in [VERIFICATION.md](./VERIFICATION.md).

To redeploy after changes:

```bash
export VERCEL_TOKEN=your_token   # https://vercel.com/account/tokens
export VERCEL_INSECURE_TLS=1     # only if corporate VPN SSL errors
./deploy-hub.sh
```

### Change the deployed URL name

Your share link is `https://<project-name>.vercel.app`. To rename it:

**Option A — Vercel dashboard (easiest)**

1. Open [vercel.com/dashboard](https://vercel.com/dashboard) → project **hub**
2. **Settings → General → Project Name**
3. Change to something like `intern-cohort` (lowercase, hyphens only)
4. Save — your new link becomes `https://intern-cohort.vercel.app`
5. Run `./deploy-hub.sh` again

**Option B — from terminal**

```bash
export HUB_PROJECT_NAME=intern-cohort   # pick your name
export VERCEL_TOKEN=your_token
export VERCEL_INSECURE_TLS=1
./deploy-hub.sh
```

Then update the README combined link to match your new URL.

Also available via [GitHub README](https://github.com/Shivendra-11/Intern-cohort) if the repo is public.

---

## Live deployments

| Project | Dashboard | Extra links |
|---------|-----------|-------------|
| **DevOps-Infra Eval** (D1–D6) | [devopsinfra-dash.vercel.app](https://devopsinfra-dash.vercel.app/) | [Services hub](https://devopsinfra-dash.vercel.app/hub) |
| **ParallelOps Eval** (A1–A6) | [parallelops-eval-dash.vercel.app](https://parallelops-eval-dash.vercel.app/) | — |
| **Polyglot Eval** (I1–I6) | [polyglot-eval.vercel.app](https://polyglot-eval.vercel.app/) | [I1 ER viewer](https://polyglot-eval-i1.vercel.app/) · [I2 Flow viewer](https://polyglot-eval-i2.vercel.app/) |
| **RepoBuilder** (B1–B6) | [repobuilder-dash.vercel.app](https://repobuilder-dash.vercel.app/) | [API](https://repobuilder-dash.vercel.app/api) |

> Open any link above in your browser — no local setup required.

---

## Projects

### 1. [DevOps-Infra Eval](./Devops-eval/)

Six-task DevOps and infrastructure evaluation harness (Terraform, Docker Compose, CI, Kubernetes, dev environments, observability).

| | |
|---|---|
| **Command** | `/devopsinfra-eval` |
| **Tasks** | D1 Terraform · D2 Compose · D3 CI · D4 Kubernetes · D5 Dev Env · D6 Observability |
| **GitHub** | [Shivendra-11/DevopsInfra-eval](https://github.com/Shivendra-11/DevopsInfra-eval) |
| **Live** | [devopsinfra-dash.vercel.app](https://devopsinfra-dash.vercel.app/) |

```bash
cd Devops-eval
/devopsinfra-eval          # in Cursor
./deploy.sh                # refresh live dashboard
```

---

### 2. [ParallelOps Eval](./ParallelOps/)

Interactive artifact dashboard for the A1–A6 agent evaluation battery — worktrees, polyglot systems, modernization, code review, and performance profiling.

| | |
|---|---|
| **Command** | `/parallelops-eval` |
| **Tasks** | A1 Worktree Plan · A2 Worktree Execute · A3 Polyglot · A4 Modernization · A5 Code Review · A6 Perf Profiling |
| **GitHub** | [Shivendra-11/Parallelops-Eval](https://github.com/Shivendra-11/Parallelops-Eval) |
| **Live** | [parallelops-eval-dash.vercel.app](https://parallelops-eval-dash.vercel.app/) |

```bash
cd ParallelOps
/parallelops-eval          # in Cursor
./deploy-dashboard-vercel.sh
```

---

### 3. [Polyglot Eval](./polyglot-builder/)

Repo-agnostic AI agent that runs six intermediate engineering eval tasks (I1–I6) on any target repository using the Claude Agent SDK.

| | |
|---|---|
| **Command** | `/polyglot-eval` |
| **Tasks** | I1 ER Diagram · I2 Flow Trace · I3 Safe Change · I4 Polyglot Pair · I5 Dockerize · I6 Bug Diagnosis |
| **GitHub** | [Shivendra-11/PolyGlot-eval](https://github.com/Shivendra-11/PolyGlot-eval) |
| **Live** | [polyglot-eval.vercel.app](https://polyglot-eval.vercel.app/) |

```bash
cd polyglot-builder
pip install -e .
/polyglot-eval             # in Cursor
polyglot-eval deploy-ui --repo /path/to/target-repo
```

---

### 4. [RepoBuilder](./RepoBuilder/)

Reusable repo-independent agent that reads any repository and scaffolds runnable greenfield services (B1–B6).

| | |
|---|---|
| **Command** | `@repo-builder` subagent |
| **Tasks** | B1 Inventory · B2 Endpoints · B3 Tests · B4 FastAPI · B5 Node API · B6 Rust CLI |
| **GitHub** | [Shivendra-11/RepoBuilder-Eval](https://github.com/Shivendra-11/RepoBuilder-Eval) |
| **Live** | [repobuilder-dash.vercel.app](https://repobuilder-dash.vercel.app/) |

```bash
cd RepoBuilder
pip install -e .
repo-intelligence analyze /path/to/target-repo
./scripts/serve-dashboard.sh
```

---

## Repository layout

```
Intern-cohort/
├── README.md                 ← this file
├── .gitignore
├── Devops-eval/              ← D1–D6 DevOps-Infra eval
├── ParallelOps/              ← A1–A6 ParallelOps eval
├── polyglot-builder/         ← I1–I6 Polyglot eval
└── RepoBuilder/              ← B1–B6 Repo intelligence & scaffolding
```

Each subfolder is a self-contained project with its own README, eval reports, dashboard, and deploy scripts. See the project README for prerequisites, task details, and verification steps.

---

## Prerequisites (shared)

| Tool | Used by |
|------|---------|
| **Python 3.10+** | All four projects |
| **Node.js 18+** | Dashboards & Vercel deploy |
| **Docker** | Devops-eval (D2, D6), Polyglot (I5) |
| **Cursor / Claude Code** | Agent orchestrator commands |
| **VERCEL_TOKEN** | Redeploy live dashboards |

---

## Quick start

```bash
# Clone this monorepo
git clone https://github.com/Shivendra-11/Intern-cohort.git
cd Intern-cohort

# Pick a project and follow its README
cd Devops-eval && cat README.md
cd ../ParallelOps && cat README.md
cd ../polyglot-builder && cat README.md
cd ../RepoBuilder && cat README.md
```

---

## Author

**Shivendra Keshari** — Intern Cohort AI Agent Evaluation Projects

