# Verification

Independently reproduced test results for every project in this monorepo.
Run everything yourself from a clean checkout with a single command:

```bash
make install   # builds an isolated .venv and installs every dependency (first time only)
make test      # runs every suite below; Node/Rust skip gracefully if absent
```

`make test` exits non-zero if any suite fails.

**Reproducible from a fresh clone.** `make install` auto-selects a Python ≥3.10
interpreter (verified here with `python3.12`), creates a self-contained `.venv`, and
editable-installs both packages — including RepoBuilder's tree-sitter `inventory`
extra — plus every lane dependency. It never depends on, or writes to, the system
Python. The full `rm -rf .venv && make install && make test` cycle was re-run on
2026-06-21 and exits 0 with **201 passed, 0 failed, 0 skipped**.

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

The I1 ER-diagram scanner ([`polyglot-builder/polyglot_eval/repo_scanner.py`](polyglot-builder/polyglot_eval/repo_scanner.py))
now extracts Python entity columns with the `ast` module instead of a line regex, so
**only class-level fields** are reported (method-local variables no longer leak in as
columns) and each column carries its real annotated type (`int`/`str`/`bool`). The
committed proof artifact
([`polyglot-builder/examples/proof-of-execution/reports/I1_er_diagram.md`](polyglot-builder/examples/proof-of-execution/reports/I1_er_diagram.md))
was regenerated from the fixture to match.

The four live dashboards were reachability-checked on 2026-06-21 — all return HTTP 200
with their correct app shells (DevOps-Infra / ParallelOps / Repo Intelligence /
polyglot-eval). They are client-rendered SPAs, so panel contents render in-browser.

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

A **root** workflow (`.github/workflows/ci.yml`) now runs the headline
`make install && make test` (all 201 tests) from a fresh clone on every push, so
the green-suite result above is externally attested by GitHub Actions — not only
re-run locally. Per-project workflows also run: `ParallelOps/.github/workflows/ci.yml`
and `Devops-eval/d3-ci-pipeline/.github/workflows/ci.yml`.

## Read-side tasks proven on a real, unfamiliar repo

The committed proof artifacts elsewhere run on author-authored fixtures. To
satisfy the eval doc's *"unfamiliar repo"* framing, the deterministic (no-model-call)
scanners were also run against [`tiangolo/full-stack-fastapi-template`](https://github.com/tiangolo/full-stack-fastapi-template)
@ `2a56db2`: B1/B2/B3 (`repo-intelligence analyze`) and I1/I2 (`repo_scanner`).
Reports, captured wall-clock, and a one-command reproducer live in
[`examples/external-repo/`](examples/external-repo/). It found 258 artifacts, 22
entities (typed + source-cited), 18 routes, and a valid Mermaid ER + sequence
diagram — in ~1.1 s, on a codebase outside this monorepo. The route scanner only
counts real routing constructs (decorators, recognised router objects, mount
prefixes, front-end `path=`/`to=` attributes), and the ER step reports
relationships **only where a foreign-key column actually resolves to a discovered
entity** — for this repo that is honestly zero, rather than placeholder edges.
