#!/usr/bin/env python3
"""Tests for core.dashboard_data_builder."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.dashboard_data_builder import (  # noqa: E402
    SCHEMA_VERSION,
    DashboardDataBuilder,
)

PY_APP = os.path.join(HERE, "fixtures", "py_app")
WORKSPACE_PY_APP = os.path.join(ROOT, "workspace", "py_app")


class TestDashboardDataBuilder(unittest.TestCase):
    def test_merge_from_existing_workspace(self):
        if not os.path.isdir(WORKSPACE_PY_APP):
            self.skipTest("workspace/py_app not populated — run agents first")

        result = DashboardDataBuilder(workspace_root=os.path.join(ROOT, "workspace")).build(
            PY_APP
        )
        self.assertTrue(os.path.isfile(result.output_path))
        data = result.payload

        self.assertEqual(data["schema_version"], SCHEMA_VERSION)
        self.assertEqual(data["role"], "dashboard_ssot")
        self.assertEqual(data["repo_name"], "py_app")
        self.assertIsNotNone(data["inventory"])
        self.assertIsNotNone(data["routes"])
        self.assertIsNotNone(data["tests"])
        self.assertIsNotNone(data["graphs"])
        self.assertIn("fastapi", data["generated_projects"])

        summary = data["summary"]
        self.assertEqual(summary["pipelines"]["B1_inventory"], "complete")
        self.assertEqual(summary["pipelines"]["B2_routes"], "complete")
        self.assertGreater(summary["counts"]["routes_total"], 0)

    def test_missing_sources_graceful(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace", "empty_repo")
            os.makedirs(ws)
            repo = os.path.join(tmp, "repos", "empty_repo")
            os.makedirs(repo)

            result = DashboardDataBuilder(workspace_root=os.path.join(tmp, "workspace")).build(
                repo,
                workspace_dir=ws,
            )
            data = result.payload
            self.assertIsNone(data["inventory"])
            self.assertIsNone(data["routes"])
            self.assertEqual(data["summary"]["pipelines"]["B1_inventory"], "missing")
            self.assertGreater(len(data["sources"]), 0)
            self.assertTrue(all(not s["present"] for s in data["sources"] if s["key"] == "inventory"))

    def test_partial_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace", "partial")
            inv_dir = os.path.join(ws, "B1_inventory")
            os.makedirs(inv_dir)
            inv_payload = {
                "repo_name": "partial",
                "counts": {"services": 1},
                "artifacts": {"services": []},
            }
            with open(os.path.join(inv_dir, "inventory.json"), "w", encoding="utf-8") as fh:
                json.dump(inv_payload, fh)

            repo = os.path.join(tmp, "repos", "partial")
            os.makedirs(repo)

            result = DashboardDataBuilder(workspace_root=os.path.join(tmp, "workspace")).build(
                repo,
                workspace_dir=ws,
            )
            self.assertIsNotNone(result.payload["inventory"])
            self.assertIsNone(result.payload["routes"])
            self.assertEqual(result.payload["summary"]["counts"]["artifacts_total"], 1)

    def test_output_written_to_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace", "disk_test")
            os.makedirs(ws)
            repo = os.path.join(tmp, "repos", "disk_test")
            os.makedirs(repo)

            result = DashboardDataBuilder(workspace_root=os.path.join(tmp, "workspace")).build(
                repo,
                workspace_dir=ws,
            )
            with open(result.output_path, encoding="utf-8") as fh:
                on_disk = json.load(fh)
            self.assertEqual(on_disk["repo_name"], "disk_test")
            self.assertEqual(on_disk["schema_version"], SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
