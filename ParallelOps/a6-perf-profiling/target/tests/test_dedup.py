"""Regression tests — behavior unchanged after perf fix."""
from dedup import dedup_txn_ids as dedup_fast
from dedup_slow import dedup_txn_ids as dedup_slow


def test_both_implementations_match():
    sample = ["a", "b", "a", "c", "b", "d", "a"]
    assert dedup_slow(sample) == dedup_fast(sample)


def test_empty_input():
    assert dedup_slow([]) == dedup_fast([]) == []


def test_all_unique():
    data = [f"id-{i}" for i in range(100)]
    assert dedup_slow(data) == dedup_fast(data)
