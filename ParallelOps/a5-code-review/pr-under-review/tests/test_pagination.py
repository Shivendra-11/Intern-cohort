"""Reproduction tests for seeded PR bugs."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.pagination import paginate  # noqa: E402


def test_page_boundary_off_by_one():
    items = list(range(10))
    page = paginate(items, page=0, page_size=3)
    assert len(page) == 3, f"expected 3 items, got {len(page)}: {page}"


def test_export_has_no_auth_gate():
    from routers.export import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    r = client.get("/transactions/export.csv")
    assert r.status_code == 200  # documents missing auth — should require 401/403


def test_threshold_invalid_order_raises():
    from routers.thresholds import validate_thresholds

    with pytest.raises(ValueError):
        validate_thresholds({"low_max": 50, "medium_max": 40, "high_min": 70})
