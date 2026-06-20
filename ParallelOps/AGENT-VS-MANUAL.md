# ParallelOps — Agent-suggested vs. manually verified

Advanced tasks (A1–A6) explicitly ask to *"separate what the agent suggested from what was
manually verified."* This is the consolidated index; A5 already carries the deepest
evidence in [`a5-code-review/verification.md`](a5-code-review/verification.md).

> The strongest proof here is **adversarial**: where the agent claimed a bug, a human ran a
> *failing* test to confirm it; where it claimed a speedup, a human re-measured.

## Per-task split

| Task | Agent produced (suggested) | Manually verified (observed) | Verification command / evidence |
|------|----------------------------|------------------------------|---------------------------------|
| **A1** Worktree plan | 3-lane decomposition, per-lane prompts, merge order | Zero owned-file overlap across lanes; plan executed in A3 | `a1-worktree-plan/VERIFICATION.log` |
| **A2** Parallel worktrees | two branches, independent edits | Real conflict on `app.py`, merged + tests green | `a2-parallel-worktrees/RECONCILE.md` |
| **A3** Polyglot system | FastAPI → queue → Node → Rust + contract | 23 pytest + 4 Node + 6 Rust green simultaneously; integration path | `bash shared/lib/verify.sh a3-polyglot` |
| **A4** Modernization | findings, prioritized plan, PEP 621 first step | First step applied; build/tests green; rollback proven | `a4-modernization/PROOF.md`, `ROLLBACK.md` |
| **A5** Code review | 5 issues (2 blocking) + fixes | **Off-by-one reproduced with a FAILING pytest**; unauth export shown via TestClient | `a5-code-review/verification.md` |
| **A6** Perf profiling | O(n²)→O(n) dedup fix | Re-measured: 0.936 s → 0.000657 s (−99.9%); tests still green | `a6-perf-profiling/baseline.md`, `AFTER.md` |

## What was observed (re-runnable)

- `cd a3-polyglot && pytest tests` → 23 passed; `worker && node --test` → 4; `fraud-engine
  && cargo test` → 6.
- A5's `pytest tests/test_pagination.py` → **1 failed, 2 passed** — the failure *is* the
  reproduced off-by-one bug (intended).
- GitHub Actions (`.github/workflows/ci.yml`) re-runs all of the above on every push.

## What remains agent-asserted (NOT independently graded)

- The `EVAL-REPORT.md` per-task ✅ PASS table and any "estimated score" are self-reports.
  The underlying test/measurement commands above are what was actually observed.
- A5 severity classifications (blocking vs non-blocking) are the reviewer-agent's judgment;
  the *reproduction* of the two blocking issues is verified, the *prioritization* is a
  suggestion.

See [`../VERIFICATION.md`](../VERIFICATION.md) for the cross-project re-run log.
