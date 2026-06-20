#!/usr/bin/env python3
"""Tests for core.workspace_registry."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.workspace_registry import WorkspaceRegistry  # noqa: E402


class TestWorkspaceRegistry(unittest.TestCase):
    def test_list_repos_skips_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace")
            os.makedirs(os.path.join(ws, "payment-service"))
            os.makedirs(os.path.join(ws, ".repo-intelligence"))
            with open(os.path.join(ws, "payment-service", "dashboard_data.json"), "w") as fh:
                json.dump({"repo_name": "payment-service", "summary": {}}, fh)

            reg = WorkspaceRegistry(ws)
            repos = reg.list_repos()
            self.assertEqual(len(repos), 1)
            self.assertEqual(repos[0].id, "payment-service")


if __name__ == "__main__":
    unittest.main(verbosity=2)
