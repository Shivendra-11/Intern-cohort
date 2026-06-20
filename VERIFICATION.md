# Verification

Independently reproduced test results for every project in this monorepo.
Run everything yourself from a clean checkout with a single command:

```bash
make install   # editable-install the two Python packages (first time only)
make test      # runs every suite below; Node/Rust skip gracefully if absent
```

`make test` exits non-zero if any suite fails.

## Results (last verified 2026-06-21)

| Suite | Command | Result |
|-------|---------|--------|
| RepoBuilder (B1–B6) | `cd RepoBuilder && python3 -m pytest tests` | **85 passed** |
| polyglot-builder (I1–I6) | `cd polyglot-builder && python3 -m pytest tests` | **59 passed** |
| ParallelOps framework | `cd ParallelOps && python3 -m pytest tests` | **17 passed** |
| ParallelOps A3 polyglot (Python) | `cd ParallelOps/a3-polyglot && python3 -m pytest tests` | **23 passed** |
| ParallelOps fraud-system | `cd ParallelOps/fraud-system && python3 -m pytest tests` | **7 passed** |
| A3 Node worker | `cd ParallelOps/a3-polyglot/worker && node --test` | **4 passed** |
| A3 Rust fraud-engine | `cd ParallelOps/a3-polyglot/fraud-engine && cargo test` | **6 passed** |

**Total: 191 Python + 4 Node + 6 Rust = 201 tests, 0 failures.**

The polyglot-builder suite gained 19 contract tests
([`polyglot-builder/tests/test_i3_i6_contracts.py`](polyglot-builder/tests/test_i3_i6_contracts.py))
that pin the I3/I6 gated-write safety guarantees (gating, no commit/push,
reproduce-before-fix, file+line root-cause citation, and the mandatory agent-vs-manual
verification note).

The A3 polyglot system (FastAPI → file-queue → Node worker → Rust scorer) is
green in all three languages simultaneously — the cross-language data contract
is documented at [`ParallelOps/a3-polyglot/contract.md`](ParallelOps/a3-polyglot/contract.md).

## Agent-suggested vs. independently verified

The per-project `EVAL-REPORT.md` files contain **self-reported** scores and
status tables written by the eval orchestrators. This file records only what was
**re-run and observed** on a developer machine. Where the two agree (all suites
green), the self-reports are corroborated; the numeric "estimated score" lines in
the eval reports remain self-assessments, not externally graded results.

Each project also ships an `AGENT-VS-MANUAL.md` that splits, task by task, what the
agent *produced* from what was *manually re-run* (with the exact command):

- [`RepoBuilder/AGENT-VS-MANUAL.md`](RepoBuilder/AGENT-VS-MANUAL.md)
- [`polyglot-builder/AGENT-VS-MANUAL.md`](polyglot-builder/AGENT-VS-MANUAL.md)
- [`ParallelOps/AGENT-VS-MANUAL.md`](ParallelOps/AGENT-VS-MANUAL.md)
- [`Devops-eval/AGENT-VS-MANUAL.md`](Devops-eval/AGENT-VS-MANUAL.md)

Time-box adherence vs the eval's stated limits is tracked in [`TIMEBOX.md`](TIMEBOX.md).

## Environment

- Python 3.12, `pytest` (per-project, `pip install -e .`)
- Node.js (built-in `node --test` runner)
- Rust / Cargo (stable)

CI also runs on every push: `ParallelOps/.github/workflows/ci.yml` and
`Devops-eval/d3-ci-pipeline/.github/workflows/ci.yml`.
