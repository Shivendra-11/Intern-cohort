# A4 — Repository Modernization Plan + First Step  [90 min]

> Run via `/parallelops-eval` → select **A4** → dispatches `modernization-analyst`.

## Goal
Analyse a repo, prioritise modernization opportunities, implement the
highest-value lowest-risk first step.

## Deliverables (in this folder)
- `FINDINGS.md` — findings + a prioritised plan (ranked table with rationale).
- `first-step/` — the highest-value lowest-risk change implemented.
- `ROLLBACK.md` — exact revert steps.
- (`target-repo/` holds the sample legacy repo being modernized.)

## Step-by-step
1. Seed a small legacy `target-repo/` if empty (e.g. `setup.py` + untyped module
   + no CI).
2. Inventory it: `python3 ~/.claude/repo-builder/scripts/report.py a4-modernization/target-repo`
   → read `REPO-ANALYSIS.md`.
3. List opportunities; rank by **value × (1 / risk)** in `FINDINGS.md`.
4. Implement the top low-risk item under `first-step/` (e.g. add `pyproject.toml`
   + pin deps + a smoke test/CI).
5. Verify (tests/build pass; behavior unchanged).
6. Write `ROLLBACK.md`.

## Tools
repo-builder analysis scripts + the target's toolchain.

## Definition of done
`FINDINGS.md` has a ranked table with rationale; exactly one first step
implemented + verified; `ROLLBACK.md` gives exact revert steps.

## Time breakdown
analyze 25m · prioritize 15m · implement 30m · verify + rollback notes 20m.

## Pitfalls
- Boiling the ocean — do **one** step.
- A "first step" that is high-risk.
- No measurable verification.
