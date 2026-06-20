"""Off-by-one pagination helper (ISS-002)."""
from __future__ import annotations


def paginate(items: list, page: int, page_size: int) -> list:
    start = page * page_size
    end = start + page_size + 1  # BUG: extra element past page boundary
    return items[start:end]
