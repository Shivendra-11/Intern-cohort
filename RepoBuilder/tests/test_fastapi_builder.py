#!/usr/bin/env python3
"""Tests for core.fastapi_builder."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.fastapi_builder import FastAPIBuilder, PROJECT_FILES  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")


class TestFastAPIBuilder(unittest.TestCase):
    def test_project_file_manifest(self):
        required = {
            "app.py",
            "models.py",
            "routes.py",
            "requirements.txt",
            "README.md",
            "tests/test_create_transaction.py",
            "tests/test_get_transactions.py",
            "tests/test_balance.py",
        }
        self.assertTrue(required.issubset(set(PROJECT_FILES.keys())))

    def test_generates_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "ws", "py_app", "generated_projects", "fastapi")
            result = FastAPIBuilder(workspace_root=os.path.join(tmp, "ws")).build(
                PY_APP, output_dir=out, run_proof=False
            )
            self.assertTrue(os.path.isfile(os.path.join(out, "app.py")))
            self.assertTrue(os.path.isfile(os.path.join(out, "models.py")))
            self.assertTrue(os.path.isfile(os.path.join(out, "routes.py")))
            self.assertTrue(os.path.isfile(os.path.join(out, "status.json")))
            self.assertEqual(result.status, "GENERATED")

    def test_status_json_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "proj")
            FastAPIBuilder().build(PY_APP, output_dir=out, run_proof=False)
            with open(os.path.join(out, "status.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["project"], "fastapi")
            self.assertIn("endpoints", data)
            self.assertEqual(len(data["endpoints"]), 3)
            self.assertIn("files", data)

    def test_proof_runs_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "fastapi_proj")
            result = FastAPIBuilder().build(PY_APP, output_dir=out, run_proof=True)
            self.assertEqual(result.proof.test_exit_code, 0)
            self.assertEqual(result.status, "SUCCESS")
            self.assertGreaterEqual(result.proof.passed or 0, 3)
            self.assertEqual(result.proof.smoke_exit_code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
