# A2 — Execute Two Parallel Worktrees  [90 min]

> Run via `/parallelops-eval` → select **A2** → dispatches `worktree-planner` (execute mode).

## Goal
Actually create two parallel git worktrees, make independent changes in each,
then reconcile cleanly — including resolving a real conflict.

## Deliverables (in this folder)
- `run.sh` — the documented command sequence actually used.
- `lane-a.log`, `lane-b.log` — output captured from each lane.
- `RECONCILE.md` — merge steps, the conflict + how it was resolved, post-merge
  test result.

## Step-by-step
1. Use a seeded sample repo (create a tiny one under this folder if none given).
2. `git worktree add ../wt-lane-a -b feat/lane-a` and `…lane-b`.
3. Lane A: edit + commit its own files **and one shared file**.
4. Lane B: edit + commit its own files **and the same shared file** → real conflict.
5. `git checkout main && git merge feat/lane-a`, then `git merge feat/lane-b`,
   resolve the conflict.
6. `bash ../shared/lib/verify.sh` — tests must pass post-merge.
7. `git worktree remove ../wt-lane-a && git worktree remove ../wt-lane-b`.

## Tools
`git` (worktrees) + the sample repo's test runner.

## Definition of done
Two worktrees existed; both lanes committed; a *real* conflict was resolved;
tests pass after merge; `RECONCILE.md` shows the steps + outputs; worktrees
cleaned up.

## Time breakdown
setup 15m · lane-a 20m · lane-b 20m · merge/conflict 20m · verify + write-up 15m.

## Pitfalls
- Forgetting `git worktree remove`.
- A "conflict" with no actual overlap (nothing to demonstrate).
- Uncommitted work blocking the merge.
