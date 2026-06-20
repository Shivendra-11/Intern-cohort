#!/usr/bin/env python3
"""Tests for core.inventory_agent (B1)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.inventory_agent import CATEGORIES, InventoryAgent, InventoryItem  # noqa: E402
from core.inventory_ast import available_parsers, parse_definitions  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
TS_APP = os.path.join(HERE, "fixtures", "ts_app")


class TestInventoryAgent(unittest.TestCase):
    def test_python_fixture_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = os.path.join(tmp, "workspace")
            result = InventoryAgent(workspace_root=ws).run(PY_APP)
            out = os.path.join(ws, "py_app", "B1_inventory")

            self.assertTrue(os.path.isfile(os.path.join(out, "inventory.json")))
            self.assertTrue(os.path.isfile(os.path.join(out, "inventory.md")))
            self.assertTrue(os.path.isfile(os.path.join(out, "graph_data.json")))

            with open(os.path.join(out, "inventory.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["repo_name"], "py_app")
            self.assertIn("items", data)
            self.assertIn("artifacts", data)

            names = {i["name"] for i in data["items"]}
            self.assertIn("LedgerService", names)
            self.assertIn("TransactionIn", names)
            self.assertIn("nightly_rollup", names)

    def test_typescript_fixture_finds_controller(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = InventoryAgent(workspace_root=os.path.join(tmp, "ws")).run(TS_APP)
            names = {i.name for i in result.items}
            self.assertIn("TransactionsController", names)

    def test_item_shape(self):
        item = InventoryItem(
            name="FooService", type="services", file="src/foo.py", line=10
        )
        d = InventoryAgent._item_dict if hasattr(InventoryAgent, "_item_dict") else None
        from core.inventory_agent import InventoryResult

        payload = InventoryResult._item_dict(item)
        self.assertEqual(set(payload.keys()), {"name", "type", "file", "line", "syntactic_kind", "signature"})
        self.assertEqual(payload["type"], "services")

    def test_graph_data_structure(self):
        items = [
            InventoryItem("A", "services", "src/a.py", 1),
            InventoryItem("B", "controllers", "src/a.py", 20),
        ]
        graph = InventoryAgent.build_graph(items)
        self.assertEqual(graph["node_count"], 2)
        self.assertGreaterEqual(graph["edge_count"], 1)
        self.assertTrue(any(e["relation"] == "same_file" for e in graph["edges"]))

    def test_all_categories_present_in_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = InventoryAgent(workspace_root=os.path.join(tmp, "ws")).run(PY_APP)
            for cat in CATEGORIES:
                self.assertIn(cat, result.by_category)

    def test_markdown_contains_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = InventoryAgent(workspace_root=os.path.join(tmp, "ws")).run(PY_APP)
            md = InventoryAgent().render_markdown(result)
            self.assertIn("# Inventory — py_app", md)
            self.assertIn("## Services", md)


class TestInventoryAst(unittest.TestCase):
    def test_parse_python_main(self):
        path = os.path.join(PY_APP, "app", "main.py")
        defs = parse_definitions(path, "python")
        if defs is None:
            self.skipTest("tree-sitter-python not installed")
        names = {d.name for d in defs}
        self.assertIn("TransactionIn", names)
        self.assertIn("create_transaction", names)

    def test_available_parsers_list(self):
        parsers = available_parsers()
        self.assertIsInstance(parsers, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
