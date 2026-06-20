---
agent: A6
session_id: "20260618-gap-closure"
status: pass
---

# A6 — Performance Profiling

Targeted O(n²) → O(n) dedup fix in `target/dedup.py`.

| Metric | Before | After | Delta |
|--------|-------:|------:|------:|
| Median runtime (n=20k) | 0.936 s | 0.000657 s | **−99.9%** |
| Tests | 3 passed | 3 passed | unchanged |

Deliverables: [baseline.md](../baseline.md) · [profile/bottleneck.md](../profile/bottleneck.md) · [AFTER.md](../AFTER.md)
