#!/usr/bin/env python3
"""Tests for core.rust_builder."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.rust_builder import RustBuilder, PROJECT_FILES  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
HAS_CARGO = bool(
    __import__("shutil").which("cargo")
    or os.path.isfile(os.path.expanduser("~/.cargo/bin/cargo"))
)


class TestRustBuilder(unittest.TestCase):
    def test_manifest(self):
        required = {
            "Cargo.toml",
            "src/main.rs",
            "src/lib.rs",
            "tests/integration.rs",
            "README.md",
        }
        self.assertTrue(required.issubset(set(PROJECT_FILES.keys())))

    def test_generates_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "rust_proj")
            result = RustBuilder().build(PY_APP, output_dir=out, run_proof=False)
            self.assertTrue(os.path.isfile(os.path.join(out, "Cargo.toml")))
            self.assertTrue(os.path.isfile(os.path.join(out, "src/main.rs")))
            self.assertTrue(os.path.isfile(os.path.join(out, "tests/integration.rs")))
            self.assertTrue(os.path.isfile(os.path.join(out, "status.json")))
            self.assertEqual(result.status, "GENERATED")

    def test_status_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "rust_proj")
            RustBuilder().build(PY_APP, output_dir=out, run_proof=False)
            with open(os.path.join(out, "status.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["project"], "rust")
            self.assertEqual(data["cli"]["counts"], ["INFO", "WARN", "ERROR"])
            self.assertIn("files", data)

    @unittest.skipUnless(HAS_CARGO, "cargo not installed")
    def test_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "rust_proj")
            result = RustBuilder().build(PY_APP, output_dir=out, run_proof=True)
            self.assertEqual(result.proof.test_exit_code, 0)
            self.assertEqual(result.proof.smoke_exit_code, 0)
            self.assertEqual(result.status, "SUCCESS")
            self.assertGreaterEqual(result.proof.passed or 0, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
