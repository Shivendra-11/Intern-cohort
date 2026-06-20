# A5 — Agent Code Review + Adversarial Verification  [60 min]

> Run via `/parallelops-eval` → select **A5** → dispatches `adversarial-reviewer`.

## Goal
Review an AI-generated PR for correctness, security, test, performance, and
maintainability issues — and adversarially verify at least one.

## Deliverables (in this folder)
- `REVIEW.md` — issue list with **severity** labels, a concrete fix per issue,
  and a verification step per issue.
- `verification.md` — the adversarial proof (commands + output) for reproduced bugs.
- (`pr-under-review/` holds the diff/PR being reviewed.)

## Step-by-step
1. Place a plausible AI-generated diff under `pr-under-review/` with seeded issues:
   an off-by-one, a missing auth check, an untested branch, an O(n²) loop, a
   naming/maintainability smell.
2. Review across correctness / security / test / perf / maintainability.
3. For each issue: severity (Critical/High/Med/Low) + concrete fix + verification.
4. Adversarially reproduce ≥1 bug (failing test / crafted input / complexity math).
5. Optionally run `/code-review` as a cross-check and reconcile.

## Tools
Read/Grep, the project's tests, optional `/code-review` skill.

## Definition of done
`REVIEW.md` lists each issue with severity + fix + verification; the seeded bugs
are caught; the adversarial step proves a bug with evidence.

## Time breakdown
read PR 15m · per-category pass 25m · fixes + verification 20m.

## Pitfalls
- Style nitpicks over real bugs.
- Severity inflation.
- "Looks fine" with no executed proof.
