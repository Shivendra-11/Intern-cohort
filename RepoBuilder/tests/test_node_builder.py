#!/usr/bin/env python3
"""Tests for core.node_builder."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.node_builder import PROJECT_FILES, NodeBuilder  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")


class TestNodeBuilder(unittest.TestCase):
    def test_manifest(self):
        required = {
            "server.js",
            "package.json",
            "routes/transactions.js",
            "README.md",
            "tests/test_create.test.js",
            "tests/test_list.test.js",
            "tests/test_balance.test.js",
        }
        self.assertTrue(required.issubset(set(PROJECT_FILES.keys())))

    def test_generates_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "node_proj")
            result = NodeBuilder().build(PY_APP, output_dir=out, run_proof=False)
            self.assertTrue(os.path.isfile(os.path.join(out, "server.js")))
            self.assertTrue(os.path.isfile(os.path.join(out, "routes/transactions.js")))
            self.assertTrue(os.path.isfile(os.path.join(out, "status.json")))
            self.assertEqual(result.status, "GENERATED")

    def test_status_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "node_proj")
            NodeBuilder().build(PY_APP, output_dir=out, run_proof=False)
            with open(os.path.join(out, "status.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["project"], "node")
            self.assertEqual(data["stack"]["validation"], "zod")
            self.assertEqual(len(data["endpoints"]), 3)

    def test_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "node_proj")
            result = NodeBuilder().build(PY_APP, output_dir=out, run_proof=True)
            self.assertEqual(result.proof.test_exit_code, 0)
            self.assertEqual(result.status, "SUCCESS")
            self.assertGreaterEqual(result.proof.passed or 0, 3)
            self.assertEqual(result.proof.smoke_exit_code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
