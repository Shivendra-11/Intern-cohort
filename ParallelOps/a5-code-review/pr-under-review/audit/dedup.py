"""O(n²) dedup scan for audit entries (ISS-004)."""
from __future__ import annotations


def dedup_entries(entries: list[dict]) -> list[dict]:
    unique: list[dict] = []
    for entry in entries:
        duplicate = False
        for seen in unique:
            if seen.get("txn_id") == entry.get("txn_id"):
                duplicate = True
                break
        if not duplicate:
            unique.append(entry)
    return unique
