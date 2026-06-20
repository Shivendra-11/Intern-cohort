"""Tests for GET/PUT /config/thresholds."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def thresholds_client(tmp_path, monkeypatch):
    config_file = tmp_path / "thresholds.json"
    monkeypatch.setenv("A3_QUEUE_DIR", str(tmp_path / "queue"))
    import routers.thresholds as thresholds_mod

    importlib.reload(thresholds_mod)
    monkeypatch.setattr(thresholds_mod, "CONFIG_FILE", config_file)
    app = FastAPI()
    app.include_router(thresholds_mod.router)
    return TestClient(app), config_file


def test_get_defaults_when_file_absent(thresholds_client):
    client, config_file = thresholds_client
    assert not config_file.exists()
    r = client.get("/config/thresholds")
    assert r.status_code == 200
    assert r.json() == {"low_max": 30, "medium_max": 70, "high_min": 71}


def test_put_persists_and_get_returns(thresholds_client):
    client, config_file = thresholds_client
    body = {"low_max": 20, "medium_max": 60, "high_min": 80}
    put = client.put("/config/thresholds", json=body)
    assert put.status_code == 200
    assert config_file.exists()
    assert client.get("/config/thresholds").json() == body


def test_put_invalid_order_returns_422(thresholds_client):
    client, _ = thresholds_client
    r = client.put(
        "/config/thresholds",
        json={"low_max": 50, "medium_max": 40, "high_min": 70},
    )
    assert r.status_code == 422


def test_put_out_of_range_returns_422(thresholds_client):
    client, _ = thresholds_client
    r = client.put(
        "/config/thresholds",
        json={"low_max": 0, "medium_max": 50, "high_min": 101},
    )
    assert r.status_code == 422
