# ParallelOps Framework (A1 + A2)

Production-grade multi-agent worktree orchestration for this repo.

## Architecture

```
User → /parallelops-eval → questions
         ↓
    A1PlannerAgent  (plan only — no code, no branches)
         ↓
    .parallelops/artifacts/a1_execution_plan.yaml
         ↓
    A2ExecutorAgent  (execute only — never replans)
         ↓
    worktrees → lane agents → merge → verify
         ↓
    .parallelops/reports/final_summary.md
```

## Setup

### Other repo — one command

From the ParallelOps repo:

```bash
~/Desktop/ParallelOps/install-parallelops.sh /path/to/your-other-repo
```

This copies `parallelops/`, the Cursor skill, `.gitignore` entries, creates
`.venv-framework`, and runs `parallelops.cli init`.

Use `--global-skill` to install `/parallelops-eval` into `~/.cursor/skills/` so
it works in **any** repo you open in Cursor:

```bash
~/Desktop/ParallelOps/install-parallelops.sh /path/to/your-other-repo --global-skill
```

### Manual setup (this repo)

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-framework
. .venv-framework/bin/activate
pip install -r requirements-framework.txt
python -m parallelops.cli init
```

## Quick start

### Interactive (recommended)

```bash
# 1. Plan
python -m parallelops.cli plan -t "Add CSV export, thresholds, and audit log to a3-polyglot"

# 2. Execute — creates worktrees + lane prompts
python -m parallelops.cli execute

# 3. Open each lane prompt in Cursor agents, implement, commit in worktree
#    .parallelops/sessions/<session>/lane_*/agent_prompt.md

# 4. Re-run execute to merge + verify
python -m parallelops.cli execute
```

### One-shot automatic demo

```bash
python -m parallelops.cli run -t "Demo parallel lanes" --mode automatic --max-lanes 2
```

### Via Cursor skill

Type `/parallelops-eval` — pick agent **A1–A6** (or custom worktree pipeline), choose mode, then the orchestrator dispatches the matching subagent and updates `EVAL-REPORT.md`.

For **custom worktree pipeline** in any repo: pick Custom in the agent menu → 9 discovery questions → A1 plan → approve → A2 execute → `final_summary.md`

## Artifact schema

`a1_execution_plan.yaml` includes:

- `task`, `parallel_lanes`, `branch_names`, `worktree_names`
- `agent_prompts`, `shared_constraints`, `ownership_rules`
- `merge_order`, `risk_plan`, `verification_plan`

## Directory layout

```text
.parallelops/
  artifacts/     a1_execution_plan.yaml, lane_prompts/
  sessions/      per-run lane outputs
  reports/       final_summary.md, conflict reports
  logs/          git + verify logs
  worktrees/     git worktree checkouts
  dashboard/     future UI
parallelops/     Python framework (A1, A2, CLI)
```

## Rules

| Agent | May | Must not |
|-------|-----|----------|
| A1 | Write YAML + prompts | Create branches, edit app code |
| A2 | Worktrees, merge, verify | Invent plan, change merge order |

## Tests

```bash
python3 -m pytest tests/test_parallelops_framework.py -q
```
