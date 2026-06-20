#!/usr/bin/env python3
"""Tests for repo-intelligence CLI."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from cli.analyze import run_analyze  # noqa: E402
from cli.main import build_parser, main  # noqa: E402
from cli.state import load_state  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")


class TestCliParser(unittest.TestCase):
    def test_parser_commands(self):
        p = build_parser()
        args = p.parse_args(["analyze", "/tmp/foo", "--no-serve"])
        self.assertEqual(args.command, "analyze")
        self.assertTrue(args.no_serve)

    def test_list_command(self):
        self.assertEqual(main(["list"]), 0)


class TestCliAnalyze(unittest.TestCase):
    def test_analyze_pipeline_no_serve(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace")
            result = run_analyze(
                PY_APP,
                workspace_root=ws,
                run_tests=False,
                builder_proof=False,
            )
            self.assertTrue(os.path.isfile(result.dashboard_path))
            with open(result.dashboard_path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["repo_name"], "py_app")
            self.assertIsNotNone(data["inventory"])
            self.assertGreater(len(result.steps), 5)

            state = load_state(Path(ws) / ".repo-intelligence")
            self.assertIsNotNone(state)
            self.assertEqual(state.repo_name, "py_app")

    def test_clean_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "workspace"
            run_analyze(PY_APP, workspace_root=str(ws), run_tests=False, builder_proof=False)
            target = ws / "py_app"
            self.assertTrue(target.is_dir())
            shutil.rmtree(target)
            self.assertFalse(target.is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
