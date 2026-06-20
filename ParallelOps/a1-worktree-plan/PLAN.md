# A1 — Multi-Worktree Parallel Plan  [45 min]  (planning only)

> Run via `/parallelops-eval` → select **A1** → dispatches `worktree-planner` (plan mode).
> No code changes; this task produces planning artifacts only.

## Goal
Split a feature task safely into parallel worktrees/agent sessions so multiple
agents can work without colliding.

## Deliverables (in this folder)
- `decomposition.md` — the feature broken into 2–3 independent lanes; per lane:
  files it owns + files it must NOT touch.
- `lanes/lane-a.prompt.md`, `lane-b.prompt.md`, (`lane-c.prompt.md`) — a complete,
  self-contained agent prompt per lane (goal, allowed files, forbidden files,
  acceptance check).
- `constraints.md` — shared rules (lint, commit convention, no shared-schema edits
  without sign-off, test gate).
- `merge-plan.md` — branch names (`feat/<lane>`), merge order, expected conflict
  points + resolution policy, verification plan run after each merge.

## Step-by-step
1. Pick a representative feature (e.g. *"add export-to-CSV + a settings page + an
   audit log"*).
2. Decompose into 2–3 lanes minimizing shared files.
3. Name branches `feat/<lane>`.
4. Write one agent prompt per lane with explicit do / don't-touch file lists.
5. Define shared constraints.
6. Define merge order + conflict plan + verification plan.

## Tools
Markdown only — pure design, no execution.

## Definition of done
A reviewer could hand each `lane-*.prompt.md` to a separate agent and the lanes
would not collide; merge order + conflict plan + verification plan are explicit.

## Time breakdown
decompose 15m · lane prompts 15m · constraints/merge/conflict/verify 15m.

## Pitfalls
- Lanes sharing the same hot file.
- Vague "don't break anything" constraints.
- No merge order → merge hell.
