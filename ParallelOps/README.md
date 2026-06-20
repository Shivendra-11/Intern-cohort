<h1 align="center">ParallelOps</h1>

<p align="center">
  <strong>Interactive artifact dashboard for the A1–A6 agent evaluation battery.</strong><br/>
  Charts, reports, execution history, and per-agent deliverables in one place.
</p>

<p align="center">
  <a href="https://parallelops-eval-dash.vercel.app/"><img src="https://img.shields.io/badge/Live_Dashboard-parallelops--eval--dash.vercel.app-6366f1?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Dashboard" /></a>
</p>

## Live deployment

| | |
|---|---|
| **Eval dashboard** | [https://parallelops-eval-dash.vercel.app/](https://parallelops-eval-dash.vercel.app/) |
| **Hosted data** | **Devliker_fullstack** — A1–A6 eval reports, charts, and session history |
| **Redeploy** | `VERCEL_TOKEN=… VERCEL_INSECURE_TLS=1 ./deploy-dashboard-vercel.sh` (bundles Devliker artifacts by default) |

Open the link above to browse pass/fail status, agent reports, and execution history — no local setup required.

---

## What is ParallelOps?

**ParallelOps** is an advanced agent evaluation framework for Cursor. It runs six engineering challenges (**A1–A6**) that test real-world skills — parallel git worktrees, polyglot system design, modernization, adversarial code review, and performance profiling — through a single interactive command:

```text
/parallelops-eval
```

The orchestrator asks which agent(s) to run and in what mode, dispatches a dedicated subagent per task, writes deliverables to disk, and serves a **React dashboard** that visualizes reports, charts, and execution history.

| Layer | Role |
|-------|------|
| **`/parallelops-eval`** | Cursor skill — picker UI, mode selection, subagent dispatch |
| **`parallelops/`** | Python CLI — plan, execute, artifact sync, dashboard server |
| **`.parallelops/dashboard/`** | React + Vite dashboard — reads `report.json` / `report.md` artifacts |
| **`a1-worktree-plan/` … `a6-perf-profiling/`** | Task folders — plans, code, proofs per agent |
| **`a3-polyglot/`** | Showcase polyglot system — FastAPI → Node → Rust fraud scorer |

Full framework docs: [PARALLELOPS-FRAMEWORK.md](PARALLELOPS-FRAMEWORK.md)

---

## The six agents (A1–A6)

| ID | Task | Time-box | Folder | Subagent |
|----|------|----------|--------|----------|
| **A1** | Multi-worktree parallel plan | 45m | [a1-worktree-plan/](a1-worktree-plan/PLAN.md) | `worktree-planner` |
| **A2** | Execute two parallel worktrees | 90m | [a2-parallel-worktrees/](a2-parallel-worktrees/PLAN.md) | `worktree-planner` |
| **A3** | Polyglot mini-system (FastAPI + Node + Rust) | 150m | [a3-polyglot/](a3-polyglot/README.md) | `polyglot-builder` |
| **A4** | Repository modernization + first step | 90m | [a4-modernization/](a4-modernization/PLAN.md) | `modernization-analyst` |
| **A5** | Agent code review + adversarial verify | 60m | [a5-code-review/REVIEW.md](a5-code-review/REVIEW.md) | `adversarial-reviewer` |
| **A6** | Performance profiling + targeted fix | 90m | [a6-perf-profiling/baseline.md](a6-perf-profiling/baseline.md) | `perf-profiler` |

**Recommended order:** `A1 → A2 → A3 → A5 → A6 → A4`

Scorecard: [EVAL-REPORT.md](EVAL-REPORT.md)

---

## Architecture

```
User → /parallelops-eval (Cursor skill)
         │  pick agent A1–A6 + mode (Plan | Build | Build + Verify)
         ▼
   Subagents: worktree-planner · polyglot-builder · modernization-analyst ·
              adversarial-reviewer · perf-profiler
         │  write deliverables + report.json / report.md
         ▼
   .parallelops/artifacts/  ──sync──▶  Dashboard UI (React + Recharts)
         │
         └── eval-finish → index.json → localhost:3000 or https://parallelops-eval-dash.vercel.app/
```

**A3 data flow (polyglot showcase):**

```
UI (index.html) ──POST /transaction──▶ FastAPI
        ▲                                   │ file queue
        │ GET /transaction/<id>             ▼
        └──────── score ◀───── Rust engine ◀── Node worker
```

---

## Local setup

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| **Python** | 3.12 | `python3.12` — avoid system Python 3.9 on macOS |
| **Node.js** | 20+ | Dashboard + A3 worker |
| **Rust / Cargo** | 1.78+ | A3 fraud engine |
| **Cursor IDE** | latest | For `/parallelops-eval` skill |
| **Git** | 2.x | Worktree tasks (A1, A2) |

### 1. Clone and install the framework

```bash
git clone https://github.com/YOUR_USERNAME/ParallelOps.git
cd ParallelOps

# One-command setup: venv, pip deps, parallelops init, Cursor skill, .gitignore
./install-parallelops.sh . --global-skill
```

**Manual setup** (if you prefer):

```bash
python3.12 -m venv .venv-framework
source .venv-framework/bin/activate
pip install -r requirements-framework.txt
python -m parallelops.cli init
```

### 2. Run the eval dashboard locally

```bash
cd .parallelops/dashboard
npm install
npm run dev
```

Open **http://localhost:3000** — the dashboard reads artifacts from `.parallelops/artifacts/` and auto-refreshes every 3 seconds.

**Sync artifacts after an eval run:**

```bash
source .venv-framework/bin/activate
python -m parallelops.cli eval-finish
# writes dashboard URL to .parallelops/artifacts/dashboard_url.txt
```

### 3. Run agents in Cursor

Open this repo in Cursor and type:

```text
/parallelops-eval
```

Pick an agent (A1–A6, All, or Custom worktree), choose mode, and the orchestrator dispatches the matching subagent.

### 4. A3 polyglot demo (FastAPI + Node + Rust)

```bash
cd a3-polyglot
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cargo build --manifest-path fraud-engine/Cargo.toml

# Terminal 1 — API
uvicorn main:app --reload --port 8000

# Terminal 2 — worker
node worker/index.js

# Terminal 3 — UI
open ui/index.html
```

Submit a transaction in the UI; watch the pipeline light up FastAPI → Node → Rust. Details: [a3-polyglot/README.md](a3-polyglot/README.md).

### 5. Install ParallelOps in another repo

```bash
./install-parallelops.sh /path/to/your-other-repo --global-skill
```

Then open that repo in Cursor and run `/parallelops-eval`.

---

## Deploy live dashboard (Vercel)

Bundle eval artifacts and deploy the static dashboard. **By default** the script bundles artifacts from **Devliker_fullstack** (the primary eval target repo), not from this ParallelOps framework repo.

```bash
# In Devliker_fullstack (or any target repo): refresh artifacts first
cd ~/Desktop/Devliker_fullstack
source /path/to/ParallelOps/.venv-framework/bin/activate   # if needed
python -m parallelops.cli eval-finish

# Deploy Devliker dashboard (default artifact source)
cd ~/Desktop/ParallelOps
VERCEL_TOKEN=your_token VERCEL_INSECURE_TLS=1 ./deploy-dashboard-vercel.sh

# Deploy a different repo's artifacts explicitly
VERCEL_TOKEN=your_token ./deploy-dashboard-vercel.sh /path/to/other-repo

# Override default repo without a CLI arg
PARALLELOPS_ARTIFACTS_REPO=/path/to/repo VERCEL_TOKEN=your_token ./deploy-dashboard-vercel.sh
```

**Production URL:** [https://parallelops-eval-dash.vercel.app/](https://parallelops-eval-dash.vercel.app/)

---

## Project structure

```
ParallelOps/
├── README.md                    ← you are here (GitHub landing page)
├── PARALLELOPS-FRAMEWORK.md     ← A1/A2 worktree orchestration
├── EVAL-REPORT.md               ← scorecard for A1–A6 runs
├── install-parallelops.sh       ← one-command installer for any repo
├── deploy-dashboard-vercel.sh   ← deploy dashboard to Vercel
├── parallelops/                   ← Python framework (CLI, artifacts, dashboard server)
├── .parallelops/
│   ├── artifacts/               ← eval reports (JSON + MD) consumed by dashboard
│   └── dashboard/               ← React + Vite + Tailwind dashboard app
├── a1-worktree-plan/            ← A1 deliverables
├── a2-parallel-worktrees/       ← A2 deliverables
├── a3-polyglot/                 ← A3 polyglot fraud-scoring system
├── a4-modernization/            ← A4 modernization analysis + first step
├── a5-code-review/              ← A5 adversarial review task
├── a6-perf-profiling/           ← A6 performance profiling task
├── fraud-system/                ← alternate polyglot layout (curl-based demo)
├── shared/lib/                  ← verify.sh, timer.sh, report.py utilities
└── .cursor/skills/              ← parallelops-eval Cursor skill
```

---

## Tech stack

| Area | Stack |
|------|-------|
| Framework | Python 3.12, Click CLI |
| Dashboard | React 19, Vite 6, TypeScript, Tailwind CSS 4, Recharts, shadcn/ui |
| A3 pipeline | FastAPI, Node.js 20, Rust |
| Deploy | Vercel — [parallelops-eval-dash.vercel.app](https://parallelops-eval-dash.vercel.app/) (Devliker_fullstack artifacts) |
| IDE integration | Cursor skills + subagents |

---

## Git branching

- `main` = integration branch
- One branch per task: `task/a1-worktree-plan` … `task/a6-perf-profiling`
- A2 demo worktrees: `feat/lane-a`, `feat/lane-b`
- Conventional commits; merge when `shared/lib/verify.sh` passes

---

## License

MIT — use freely for evaluation, demos, and extension.
