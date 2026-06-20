#!/usr/bin/env python3
"""Tests for core.test_agent (B3)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.test_agent import TestAgent  # noqa: E402
from core.test_discovery import TestDiscovery  # noqa: E402
from core.test_interpreter import interpret_failures, parse_counts  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
TS_APP = os.path.join(HERE, "fixtures", "ts_app")


class TestTestDiscovery(unittest.TestCase):
    def test_detect_pytest(self):
        setups = TestDiscovery().discover(PY_APP)
        self.assertTrue(setups)
        self.assertEqual(setups[0].framework, "pytest")
        self.assertTrue(any("test_balance.py" in f for f in setups[0].test_files))

    def test_detect_jest(self):
        setups = TestDiscovery().discover(TS_APP)
        frameworks = {s.framework for s in setups}
        self.assertIn("jest", frameworks)


class TestInterpreter(unittest.TestCase):
    def test_parse_pytest_output(self):
        output = "1 passed in 0.01s"
        counts = parse_counts("pytest", output)
        self.assertEqual(counts.passed, 1)

    def test_parse_jest_output(self):
        output = "Tests: 2 failed, 10 passed, 12 total"
        counts = parse_counts("jest", output)
        self.assertEqual(counts.failed, 2)
        self.assertEqual(counts.passed, 10)

    def test_interpret_snapshot_failure(self):
        text = interpret_failures(
            "jest",
            "Snapshot name: `Foo 1`\n3 snapshots failed",
            1,
            parse_counts("jest", "Tests: 3 failed, 5 passed"),
        )
        self.assertIn("Snapshot", text)


class TestTestAgent(unittest.TestCase):
    def test_output_files_discovery_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = TestAgent(workspace_root=os.path.join(tmp, "ws")).run(
                PY_APP, execute=False
            )
            out = os.path.join(tmp, "ws", "py_app", "B3_tests")
            self.assertTrue(os.path.isfile(os.path.join(out, "tests.json")))
            self.assertTrue(os.path.isfile(os.path.join(out, "tests.md")))
            self.assertTrue(os.path.isfile(os.path.join(out, "test_output.log")))
            self.assertEqual(result.execution.status, "SKIPPED")

    def test_tests_json_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            TestAgent(workspace_root=os.path.join(tmp, "ws")).run(
                PY_APP, execute=False
            )
            with open(
                os.path.join(tmp, "ws", "py_app", "B3_tests", "tests.json"),
                encoding="utf-8",
            ) as fh:
                data = json.load(fh)
            self.assertEqual(data["framework"], "pytest")
            self.assertIn("execution", data)
            self.assertIn("test_files", data)

    def test_execute_pytest_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = TestAgent(workspace_root=os.path.join(tmp, "ws")).run(
                PY_APP, execute=True, skip_install=False
            )
            self.assertEqual(result.primary.framework, "pytest")
            self.assertEqual(result.execution.exit_code, 0)
            self.assertEqual(result.execution.status, "SUCCESS")
            log = result.execution.combined_log()
            self.assertIn("stdout", log)
            self.assertIn("=== stderr ===", log)

    def test_log_file_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            TestAgent(workspace_root=os.path.join(tmp, "ws")).run(PY_APP)
            with open(
                os.path.join(tmp, "ws", "py_app", "B3_tests", "test_output.log"),
                encoding="utf-8",
            ) as fh:
                content = fh.read()
            self.assertIn("exit_code:", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
