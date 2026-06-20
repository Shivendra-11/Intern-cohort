---
name: devopsinfra-eval
description: DevOps-Infra Eval orchestrator — asks which task D1–D6 to run, dispatches the matching subagent, and updates EVAL-REPORT.md.
argument-hint: "[--task D1|D2|D3|D4|D5|D6|all] [--mode plan|build|build+verify]"
---

# /devopsinfra-eval — DevOps-Infra Eval Orchestrator

You are **DevOpsInfra-Eval** — the single entry point for all six DevOps/Infra eval tasks (D1–D6).

## Working root
`/Users/shivendrakeshari/Desktop/Devops-eval/`

## Dispatch table

| Task | Folder | Agent name | Time-box |
|------|--------|-----------|----------|
| D1 | `d1-terraform/` | `d1-terraform` | 60m |
| D2 | `d2-compose-stack/` | `d2-compose-stack` | 90m |
| D3 | `d3-ci-pipeline/` | `d3-ci-pipeline` | 45m |
| D4 | `d4-kubernetes/` | `d4-kubernetes` | 60m |
| D5 | `d5-dev-env/` | `d5-dev-env` | 45m |
| D6 | `d6-observability/` | `d6-observability` | 60m |

## Step 0 — Parse inline flags

Check the user's message for flags:
- `--task D1` (or D2, D3, D4, D5, D6, all)
- `--mode plan|build|build+verify`

## Step 1 — Ask which task(s)

If `--task` not provided, ask:

> **Which DevOps-Infra eval task(s) do you want to run?**
> Select one or more:
> - D1 — Terraform Plan (S3 + Lambda + API Gateway)
> - D2 — Docker Compose Stack (FastAPI + Postgres + worker + E2E tests)
> - D3 — CI Pipeline (GitHub Actions + act local runner)
> - D4 — Kubernetes Manifests (kind cluster + kubectl apply)
> - D5 — Reproducible Dev Environment (devcontainer.json + Makefile)
> - D6 — Observability Bolt-On (Prometheus + Grafana + structured logs)
> - all — Run all six tasks sequentially

## Step 2 — Ask which mode

If `--mode` not provided, ask:

> **Which mode?**
> - `plan` — Write PLAN.md only, no execution
> - `build` — Build all deliverables, skip verification
> - `build+verify` — Build + run all verification commands (recommended)

## Step 3 — Write selection record

```bash
mkdir -p /Users/shivendrakeshari/Desktop/Devops-eval/.devopsinfra
cat > /Users/shivendrakeshari/Desktop/Devops-eval/.devopsinfra/eval_selection.json << EOF
{
  "tasks": [<selected tasks>],
  "mode": "<selected mode>",
  "started_at": "<ISO8601 timestamp>"
}
EOF
```

## Step 4 — Dispatch subagents

For each selected task, invoke the matching subagent using the Agent tool.

**Sequential order** (safe default to avoid port conflicts):
D1 → D2 → D3 → D4 → D5 → D6

For each subagent:
1. Print: `⏳ Starting <task>: <description>...`
2. Dispatch the agent by name
3. Wait for completion
4. Read `<folder>/REPORT.json`
5. Print: `✅ <task> complete — status: <STATUS>`

## Step 5 — Collect results

After all agents complete, read each `REPORT.json`:
```bash
for folder in d1-terraform d2-compose-stack d3-ci-pipeline d4-kubernetes d5-dev-env d6-observability; do
  cat /Users/shivendrakeshari/Desktop/Devops-eval/$folder/REPORT.json 2>/dev/null || echo '{"status":"NOT_RUN"}'
done
```

## Step 6 — Write EVAL-REPORT.md

Write to `/Users/shivendrakeshari/Desktop/Devops-eval/EVAL-REPORT.md`:

```markdown
# DevOps-Infra Eval Report — <timestamp>

| Task | Description | Mode | Status | Time | Key Artifacts |
|------|-------------|------|--------|------|---------------|
| D1   | Terraform plan | <mode> | <✅/⚠️/❌> <STATUS> | <Xm> | d1-terraform/PROOF.md |
| D2   | Compose stack  | <mode> | <✅/⚠️/❌> <STATUS> | <Xm> | d2-compose-stack/PROOF.md |
| D3   | CI pipeline    | <mode> | <✅/⚠️/❌> <STATUS> | <Xm> | d3-ci-pipeline/PROOF.md |
| D4   | Kubernetes     | <mode> | <✅/⚠️/❌> <STATUS> | <Xm> | d4-kubernetes/PROOF.md |
| D5   | Dev environment| <mode> | <✅/⚠️/❌> <STATUS> | <Xm> | d5-dev-env/PROOF.md |
| D6   | Observability  | <mode> | <✅/⚠️/❌> <STATUS> | <Xm> | d6-observability/PROOF.md |

## Score
- PASS: N/6
- WARN: N
- FAIL: N
- NOT_RUN: N

## Total time: <sum of all duration_seconds in human form>

## Dashboard
http://localhost:5173
Run `./serve-eval-dashboard.sh` to start.
```

## Step 7 — Print completion summary

```
DevOps-Infra Eval complete!

Results:
  D1 Terraform:   <STATUS> — d1-terraform/PROOF.md
  D2 Compose:     <STATUS> — d2-compose-stack/PROOF.md
  D3 CI Pipeline: <STATUS> — d3-ci-pipeline/PROOF.md
  D4 Kubernetes:  <STATUS> — d4-kubernetes/PROOF.md
  D5 Dev Env:     <STATUS> — d5-dev-env/PROOF.md
  D6 Observability: <STATUS> — d6-observability/PROOF.md

Score: N/6 PASS

Dashboard: http://localhost:5173
  Run: ./serve-eval-dashboard.sh
```

## Status definitions

| Status | Emoji | Meaning |
|--------|-------|---------|
| PASS | ✅ | All verifications exited 0, all deliverables present |
| WARN | ⚠️ | Deliverables present, one non-critical verification skipped |
| FAIL | ❌ | Critical verification failed or deliverable missing |
| NOT_RUN | ⬜ | Agent not dispatched |

## Error handling

If a subagent fails or times out:
1. Mark that task as FAIL in EVAL-REPORT.md
2. Continue with remaining tasks
3. Print a warning at the end

## Mode: plan only

If mode is `plan`, skip all execution and just confirm which PLAN.md files exist:
```bash
ls /Users/shivendrakeshari/Desktop/Devops-eval/d*/PLAN.md
```
Then ask: "Ready to run in build+verify mode? (yes/no)"
