"""Inconsistent naming: get_* vs fetch_* (ISS-005)."""
from __future__ import annotations


def get_user(user_id: str) -> dict:
    return {"id": user_id}


def fetch_account(account_id: str) -> dict:
    return {"id": account_id}
