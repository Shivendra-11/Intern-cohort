# Polyglot-Eval — Agent-suggested vs. manually verified

The eval doc asks every intermediate task (notably I3 and I6) to show *"what the agent
suggested vs what was manually verified."* This file makes that separation explicit for
the framework itself, and the task specs enforce it per-run via the `verification_note`
deliverable.

> Two layers of trust here:
> 1. **The framework** (this repo) — agent-written Python, **verified** by `pytest`.
> 2. **Each eval run** on a target repo — the eval *agent's* output, which the framework
>    forces to carry its own agent-vs-manual note (see below).

## Layer 1 — the framework (verified by tests)

| Area | Agent produced (suggested) | Manually verified (observed) | Verification command |
|------|----------------------------|------------------------------|----------------------|
| Task contracts I1–I6 | `polyglot_eval/tasks/*` TaskSpecs | Registry wiring, filenames, deliverables pinned | `pytest tests/test_task_defaults.py -q` |
| I3/I6 safety guarantees | gated prompts, minimal-diff rules | Gating, no-commit rule, repro-before-fix, file+line citation all asserted | `pytest tests/test_i3_i6_contracts.py -q` |
| Permission gating | `permissions.py` deny/allow logic | Destructive bash denied; dirty tree rejected; branch auto-created | `pytest tests/test_permissions.py -q` |
| Report tools | `tools/report_tools.py` | Section validation + artifact save round-trip | `pytest tests/test_report_tools.py -q` |
| Dashboard data | `dashboard_builder.py` | Build + schema asserted | `pytest tests/test_dashboard_builder.py -q` |
| End-to-end | orchestrator wiring | Integration path green | `pytest tests/test_integration.py -q` |

Last run (2026-06-21): `pytest tests -q` → **59 passed**, 0 failed.

## Layer 2 — each eval run on a target repo

The framework does **not** let the eval agent self-certify. Every write task makes the
agent-vs-manual line a *required* report section, enforced by
[`tests/test_i3_i6_contracts.py`](tests/test_i3_i6_contracts.py):

- **I3 (safe change)** and **I6 (bug diagnosis)** both carry a `verification_note`
  deliverable whose label is literally *"Agent-suggested vs manually-verified — what a
  human reviewer should double-check."*
- Both run in **gated** permission mode (`permission_mode="default"`, `writes_repo=True`)
  — every file write needs operator approval, so no change lands unseen.
- I6 must **reproduce before fixing** (a failing test/script first) and cite the root
  cause by **exact file + line** — verified by the contract tests, not trusted.
- `commit` / `push` / `merge` are forbidden in the prompts **and** hard-denied by
  `permissions.py` — so the agent physically cannot alter history.

## What remains agent-asserted (NOT independently graded)

- For a given target repo, the *content* of an I1 ER diagram or an I2 flow trace is the
  eval agent's analysis. The framework guarantees the diagram is **valid Mermaid** and
  **cites source files**, but a human still owns the semantic correctness call.
- The per-task `status: "pass"` an eval run writes into `data.json` is the agent's
  self-report; the dashboards display it as such.

See [`../VERIFICATION.md`](../VERIFICATION.md) for the cross-project re-run log.
