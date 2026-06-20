# A6 Profiling — Bottleneck Analysis

## Approach

1. Seeded `target/dedup_slow.py` with an O(n²) dedup (nested loop over `unique`).
2. Ran `python -m cProfile -s cumtime bench.py` with `n=20_000`.
3. Inspected cumulative time to locate the hotspot before applying a minimal fix.

## What the profile showed

From `profile/cprofile_stats.txt`:

```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    9   10.083    1.120   10.092    1.121 dedup_slow.py:5(dedup_txn_ids)
    9    0.018    0.002    0.032    0.004 dedup.py:5(dedup_txn_ids)
```

~99% of benchmark time sits in `dedup_slow.dedup_txn_ids`. The optimized
`dedup.py` run in the same script takes milliseconds.

## Bottleneck explanation

For each of `n` input ids, the slow version scans the entire `unique` list
built so far — worst-case O(n²) comparisons. With 20k rows and heavy
duplication this dominates CPU time.

## Targeted fix

`target/dedup.py` adds a `seen: set[str]` for O(1) membership while preserving
first-seen order in the output list. Diff is ~10 lines; no API change.

## Verification

- `bench.py` reports **99.9%** median improvement.
- `pytest tests/` — 3 passed (behaviour unchanged).
