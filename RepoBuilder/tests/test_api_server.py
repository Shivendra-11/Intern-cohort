#!/usr/bin/env python3
"""Tests for core.api_server multi-repo support."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None  # type: ignore[misc, assignment]

from core.api_server import create_app  # noqa: E402
from core.dashboard_data_builder import DashboardDataBuilder  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
TS_APP = os.path.join(HERE, "fixtures", "ts_app")


def _write_min_dashboard(path: str, repo_name: str, repo_path: str) -> None:
    payload = {
        "schema_version": "1.0",
        "role": "dashboard_ssot",
        "repo_name": repo_name,
        "repo_path": repo_path,
        "workspace_dir": os.path.dirname(path),
        "generated_at": "2026-01-01T00:00:00+00:00",
        "inventory": {"repo_name": repo_name, "counts": {"services": 1}, "artifacts": {}},
        "routes": {"repo_name": repo_name, "counts": {"total": 0}, "backend": [], "frontend": [], "routes": []},
        "tests": {"repo_name": repo_name, "framework": "none", "status": "SKIPPED", "passed": 0},
        "graphs": {"repo_name": repo_name, "engine": "networkx", "graphs": {}},
        "generated_projects": {},
        "summary": {
            "pipelines": {
                "B1_inventory": "complete",
                "B2_routes": "complete",
                "B3_tests": "complete",
                "graphs": "complete",
                "greenfield": None,
            },
            "counts": {},
        },
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


@unittest.skipUnless(TestClient is not None, "fastapi/httpx not installed")
class TestApiServerMultiRepo(unittest.TestCase):
    def test_list_and_switch_repos(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace")
            _write_min_dashboard(
                os.path.join(ws, "kyc-mini", "dashboard_data.json"),
                "kyc-mini",
                "/repos/kyc-mini",
            )
            _write_min_dashboard(
                os.path.join(ws, "stocks-mini", "dashboard_data.json"),
                "stocks-mini",
                "/repos/stocks-mini",
            )

            client = TestClient(create_app(workspace_root=ws, default_repo="kyc-mini"))

            repos = client.get("/repos").json()
            self.assertEqual(repos["count"], 2)
            self.assertEqual(repos["default"], "kyc-mini")
            ids = {r["id"] for r in repos["repos"]}
            self.assertEqual(ids, {"kyc-mini", "stocks-mini"})

            kyc = client.get("/overview?repo=kyc-mini").json()
            stocks = client.get("/overview?repo=stocks-mini").json()
            self.assertEqual(kyc["repo_name"], "kyc-mini")
            self.assertEqual(stocks["repo_name"], "stocks-mini")

    def test_legacy_single_dashboard_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace")
            dash = os.path.join(ws, "py_app", "dashboard_data.json")
            if os.path.isfile(os.path.join(ROOT, "workspace", "py_app", "dashboard_data.json")):
                DashboardDataBuilder(workspace_root=ws).build(PY_APP)
            else:
                _write_min_dashboard(dash, "py_app", PY_APP)

            client = TestClient(create_app(dashboard_path=dash))
            res = client.get("/overview")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["repo_name"], "py_app")


if __name__ == "__main__":
    unittest.main(verbosity=2)
