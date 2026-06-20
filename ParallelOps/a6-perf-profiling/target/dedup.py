"""Optimized dedup — O(n) with a set for membership checks."""
from __future__ import annotations


def dedup_txn_ids(txn_ids: list[str]) -> list[str]:
    """Return unique txn_ids preserving first-seen order."""
    unique: list[str] = []
    seen: set[str] = set()
    for txn_id in txn_ids:
        if txn_id in seen:
            continue
        seen.add(txn_id)
        unique.append(txn_id)
    return unique
