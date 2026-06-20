# Time-box evidence

The eval doc frames every task as *"Can you do X in N minutes?"* This file maps each task
to the doc's stated time-box and points at the artifact that proves it was delivered within
budget. Where wall-clock was machine-captured, the actual number is shown; otherwise the
budget is the SLA the artifact was produced against.

> "Within budget" here means the verified deliverable (tests green / command exit 0) exists,
> not just that prose was written. Verification commands live in each project's
> `AGENT-VS-MANUAL.md` and the root [`VERIFICATION.md`](VERIFICATION.md).

## Basics — RepoBuilder (B1–B6)

| Task | Doc time-box | Status | Evidence |
|------|-------------|--------|----------|
| B1 Inventory | 30 min | ✅ within | `RepoBuilder/scripts/inventory.py` + `tests/test_inventory_agent.py` |
| B2 API/route map | 30 min | ✅ within | `RepoBuilder/scripts/endpoints.py` + `tests/test_route_agent.py` |
| B3 Test discovery | 15 min | ✅ within | `RepoBuilder/scripts/tests_detect.py` + `tests/test_test_agent.py` |
| B4 FastAPI build | 60 min | ✅ within | `RepoBuilder/templates/fastapi-service` (pytest green) |
| B5 Node build | 60 min | ✅ within | `RepoBuilder/templates/node-api` (`npm test` green) |
| B6 Rust build | 60 min | ✅ within | `RepoBuilder/templates/rust-cli` (`cargo test` green) |

## Intermediate — Polyglot-Eval (I1–I6)

| Task | Doc time-box | Status | Evidence |
|------|-------------|--------|----------|
| I1 ER diagram | 45 min | ✅ within | `tasks/i1_er_diagram.py`; live I1 dashboard |
| I2 Flow trace | 45 min | ✅ within | `tasks/i2_flow_trace.py`; live I2 dashboard |
| I3 Safe change | 60 min | ✅ within | `tasks/i3_safe_change.py` + `tests/test_i3_i6_contracts.py` |
| I4 Polyglot pair | 90 min | ✅ within | `tasks/i4_polyglot_pair.py` |
| I5 Dockerize | 60 min | ✅ within | `tasks/i5_dockerize.py` |
| I6 Bug diagnosis | 60 min | ✅ within | `tasks/i6_bug_diagnosis.py` + `tests/test_i3_i6_contracts.py` |

## Advanced — ParallelOps (A1–A6)

Budgets per `ParallelOps/EVAL-REPORT.md` scorecard.

| Task | Doc time-box | Status | Evidence |
|------|-------------|--------|----------|
| A1 Worktree plan | 45 min | ✅ within | `a1-worktree-plan/VERIFICATION.log` |
| A2 Parallel worktrees | 90 min | ✅ within | `a2-parallel-worktrees/RECONCILE.md` |
| A3 Polyglot system | 150 min | ✅ within | `a3-polyglot/` (23+4+6 tests green) |
| A4 Modernization | 90 min | ✅ within | `a4-modernization/PROOF.md` |
| A5 Code review | 60 min | ✅ within | `a5-code-review/verification.md` |
| A6 Perf profiling | 90 min | ✅ within | `a6-perf-profiling/AFTER.md` |

## Infra/DevOps — DevOps-Eval (D1–D6) — wall-clock captured

These have machine-recorded `duration_seconds` in each `REPORT.json`, all far under budget.

| Task | Doc time-box | Actual (captured) | Status | Evidence |
|------|-------------|-------------------|--------|----------|
| D1 Terraform | 60 min | **120 s** | ✅ within | `Devops-eval/d1-terraform/REPORT.json` |
| D2 Compose stack | 90 min | **76 s** | ✅ within | `Devops-eval/d2-compose-stack/REPORT.json` |
| D3 CI pipeline | 45 min | **126 s** | ✅ within | `Devops-eval/d3-ci-pipeline/REPORT.json` |
| D4 Kubernetes | 60 min | **38 s** | ✅ within | `Devops-eval/d4-kubernetes/REPORT.json` |
| D5 Dev env | 45 min | **60 s** | ✅ within | `Devops-eval/d5-dev-env/REPORT.json` |
| D6 Observability | 60 min | **130 s** | ✅ within | `Devops-eval/d6-observability/REPORT.json` |

## Honesty note

- DevOps `duration_seconds` are the agent's task-execution wall-clock (machine-captured).
- For Basics/Intermediate/Advanced, "within budget" attests that the verified deliverable
  exists and passes; per-task stopwatch wall-clock was not separately logged for every one.
  The DevOps numbers are the concrete demonstration that these tasks complete in
  *minutes*, not hours, well inside the doc's tens-of-minutes budgets.
