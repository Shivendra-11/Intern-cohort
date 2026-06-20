# A6 Baseline Measurement

**Target:** `target/dedup_slow.py` — O(n²) dedup via nested scan  
**Method:** `bench.py` — warmup 2, median of 7 runs, `n=20_000` txn ids (~50% duplicates)  
**Date:** 2026-06-18

---

## Command

```bash
cd a6-perf-profiling/target
python bench.py
```

---

## Results (slow implementation only)

| Metric | Value |
|--------|------:|
| Input size (`n`) | 20,000 |
| Warmup runs | 2 |
| Measured runs | 7 (median reported) |
| **Median runtime** | **0.936 s** |
| Fast reference (same run file) | 0.000657 s |

The benchmark script runs both implementations for comparison; baseline for
optimization work is the **slow_median_s** line above.

---

## Environment

- Python 3.12.13 (`.venv-framework`)
- macOS darwin 25.5.0
- No other services involved — pure in-process CPU benchmark
