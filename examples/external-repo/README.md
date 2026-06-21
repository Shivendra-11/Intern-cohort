# Proof on a real, *unfamiliar* external repo

The eval doc frames the read-side tasks as *"in **this** repo / an **unfamiliar**
module."* The committed proof artifacts elsewhere in this monorepo run against
author-authored fixtures. This directory closes that gap: it runs the same
deterministic, **no-model-call** scanners against a third-party open-source
codebase that nobody here wrote.

## Target

| | |
|---|---|
| **Repo** | [`tiangolo/full-stack-fastapi-template`](https://github.com/tiangolo/full-stack-fastapi-template) |
| **Pinned commit** | `2a56db28b2893bff774aa7a834196cbab59ec747` |
| **Why** | Real FastAPI + SQLModel backend (DB models → good ER) **and** a TypeScript frontend (polyglot inventory) |

## Reproduce (one command, no API key)

```bash
# 1. clone the external repo at the pinned commit
git clone https://github.com/tiangolo/full-stack-fastapi-template /tmp/ext-eval-repo
git -C /tmp/ext-eval-repo checkout 2a56db28b2893bff774aa7a834196cbab59ec747

# 2. run the read-side tasks against it (uses the repo's own .venv)
make install                                              # if not already done
.venv/bin/python examples/external-repo/run_external_proof.py /tmp/ext-eval-repo backend
```

Every task here is **static analysis (AST / grep)** — zero model calls — so the
output is deterministic and re-runnable by a grader. (`I1`/`I2` via the polyglot
`repo_scanner`; `B1`/`B2`/`B3` via `repo-intelligence analyze`.)

## Results — machine-captured wall-clock

Captured by the script into [`reports/timings.json`](reports/timings.json); raw
console output in [`RUN_LOG.txt`](RUN_LOG.txt).

| Task | Doc time-box | Captured wall-clock | Output |
|------|-------------|---------------------|--------|
| B1 inventory + B2 routes + B3 tests | 30 + 30 + 15 min | **~1.1 s** | [B1_inventory.md](reports/B1_inventory.md) · [B2_routes.md](reports/B2_routes.md) · [B3_tests.md](reports/B3_tests.md) |
| I1 ER diagram | 45 min | **~0.03 s** | [I1_er_diagram.md](reports/I1_er_diagram.md) |
| I2 flow trace | 45 min | **~0.03 s** | [I2_flow_trace.md](reports/I2_flow_trace.md) |

## What it found (on a repo nobody here authored)

- **B1** — 258 artifacts, each with a `file:line` citation (classes in
  `backend/app/models.py`, services, config).
- **B2** — 19 backend routes + the frontend route set.
- **B3** — correctly detected `pytest` and the real run command.
- **I1** — 22 entities with typed, source-cited columns and a valid Mermaid ER
  diagram; PKs detected on `User`/`Item` (`id: uuid.UUID`).
- **I2** — entry points in `app/main.py` / `app/api/main.py`, 19 exposed routes,
  a 15-step flow path, and a Mermaid sequence diagram.

## Honesty note

These wall-clock numbers are the **scan/generation** time on a fresh, unseen repo
— the analogue of the DevOps `duration_seconds`. They demonstrate the read-side
tooling completes in *seconds*, far inside the doc's tens-of-minutes budgets, and
on a codebase outside this monorepo. The cloned repo itself is **not** committed
here (only the generated reports are); re-running the clone + script regenerates
them.
