"""Slow dedup — O(n²) pairwise scan (A6 bottleneck seed)."""
from __future__ import annotations


def dedup_txn_ids(txn_ids: list[str]) -> list[str]:
    """Return unique txn_ids preserving first-seen order."""
    unique: list[str] = []
    for txn_id in txn_ids:
        seen_before = False
        for existing in unique:
            if existing == txn_id:
                seen_before = True
                break
        if not seen_before:
            unique.append(txn_id)
    return unique
