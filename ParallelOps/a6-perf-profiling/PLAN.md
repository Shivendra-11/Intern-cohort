# A6 — Performance Profiling + Targeted Improvement  [90 min]

> Run via `/parallelops-eval` → select **A6** → dispatches `perf-profiler`.

## Goal
Find a real bottleneck and make a measurable, minimal improvement without a
broad rewrite.

## Deliverables (in this folder)
- `baseline.md` — baseline measurement + method.
- `profile/` — profiler output (flamegraph / py-spy dump / cProfile stats).
- the targeted fix (committed in `target/`).
- `AFTER.md` — after-measurement, before/after delta with a **stated %**, tests pass.

## Step-by-step
1. Seed `target/` with a real bottleneck (e.g. recompute-in-loop, or the A3 Rust
   scorer scaled to many txns) if empty.
2. Take a baseline (`hyperfine` / `time` / `pytest-benchmark` / `py-spy` /
   `cargo bench`) — warm up, repeat, report median.
3. Profile to localize the hotspot.
4. Explain the bottleneck.
5. Make a **minimal** targeted fix (memoize / hoist / better data structure).
6. Re-measure with the same method; keep tests green.

## Tools
`hyperfine`, `py-spy`/`cProfile`, `cargo flamegraph`/`criterion` (whichever fits).

## Definition of done
Baseline + after numbers with the same method; one localized change; measurable
improvement with a stated %; tests still pass; `AFTER.md` shows before/after.

## Time breakdown
baseline 20m · profile + localize 25m · targeted fix 20m · re-measure + tests 15m
· write-up 10m.

## Pitfalls
- Measuring noise (no warmup/repeat/median).
- Optimizing the wrong thing (skipping the profiler).
- A "minimal" fix that is actually a rewrite.
- Not re-running tests.
