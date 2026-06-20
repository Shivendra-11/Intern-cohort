# A6 After Measurement

**Fix:** `target/dedup.py` — O(n) dedup using a `set` for membership  
**Method:** Same as baseline (`bench.py`, warmup 2, median of 7, `n=20_000`)  
**Date:** 2026-06-18

---

## Command

```bash
cd a6-perf-profiling/target
python bench.py
python -m pytest tests/ -q
```

---

## Before / after

| Metric | Before (slow) | After (fast) | Delta |
|--------|----------------:|-------------:|------:|
| Median runtime | 0.936 s | 0.000657 s | **−99.9%** |
| Algorithm | O(n²) nested scan | O(n) set lookup | — |
| Tests | 3 passed | 3 passed | unchanged |

**Stated improvement:** **99.9%** reduction in median runtime for `n=20_000`.

---

## Behaviour verification

```bash
pytest tests/ -q
# 3 passed in 0.01s
```

`test_both_implementations_match` confirms slow and fast implementations return
identical output for shared inputs.

---

## Rollback

Replace imports of `dedup.dedup_txn_ids` with `dedup_slow.dedup_txn_ids` or
revert commit touching `target/dedup.py`. Tests continue to pass against either
implementation.
