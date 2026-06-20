"""Benchmark harness for A6 before/after comparison."""
from __future__ import annotations

import statistics
import time
from pathlib import Path

from dedup import dedup_txn_ids as dedup_fast
from dedup_slow import dedup_txn_ids as dedup_slow

REPEATS = 7
WARMUP = 2
N = 20_000


def _make_input(n: int) -> list[str]:
    # ~50% duplicates to exercise dedup logic
    return [f"txn-{i % (n // 2)}" for i in range(n)]


def _median_seconds(fn, data: list[str]) -> float:
    for _ in range(WARMUP):
        fn(data)
    samples = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        fn(data)
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def main() -> None:
    data = _make_input(N)
    slow_s = _median_seconds(dedup_slow, data)
    fast_s = _median_seconds(dedup_fast, data)
    pct = ((slow_s - fast_s) / slow_s) * 100 if slow_s else 0.0
    print(f"n={N} repeats={REPEATS} warmup={WARMUP}")
    print(f"slow_median_s={slow_s:.6f}")
    print(f"fast_median_s={fast_s:.6f}")
    print(f"improvement_pct={pct:.1f}")


if __name__ == "__main__":
    main()
