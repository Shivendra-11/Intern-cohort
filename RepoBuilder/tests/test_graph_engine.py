#!/usr/bin/env python3
"""Tests for core.graph_engine."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.graph_engine import GraphEngine, GraphModel  # noqa: E402
from core.inventory_agent import InventoryAgent, InventoryItem  # noqa: E402
from core.route_agent import RouteAgent  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
TS_APP = os.path.join(HERE, "fixtures", "ts_app")


class TestGraphModel(unittest.TestCase):
    def test_to_dict_shape(self):
        model = GraphModel(
            graph_type="import",
            nodes=[{"id": "a", "kind": "file"}],
            edges=[{"source": "a", "target": "b", "relation": "imports"}],
            metadata={"node_count": 1},
        )
        d = model.to_dict()
        self.assertIn("nodes", d)
        self.assertIn("edges", d)
        self.assertIn("metadata", d)


class TestGraphEngine(unittest.TestCase):
    def test_import_graph_py_app(self):
        model = GraphEngine().build_import_graph(PY_APP)
        self.assertEqual(model.graph_type, "import")
        self.assertGreater(model.metadata["node_count"], 0)
        self.assertTrue(any(n.get("kind") == "file" for n in model.nodes))

    def test_class_dependency_graph(self):
        model = GraphEngine().build_class_dependency_graph(PY_APP)
        self.assertEqual(model.graph_type, "class_dependencies")
        names = {n.get("name") for n in model.nodes}
        self.assertIn("TransactionIn", names)

    def test_service_graph_from_inventory(self):
        inv = InventoryAgent().build_inventory(PY_APP, "py_app")
        model = GraphEngine().build_service_graph(inv.items)
        self.assertEqual(model.graph_type, "service")
        types = {n.get("kind") for n in model.nodes}
        self.assertIn("services", types)

    def test_route_graph(self):
        routes = RouteAgent().discover(TS_APP, "ts_app").all_routes
        model = GraphEngine().build_route_graph(routes)
        self.assertGreater(model.metadata["node_count"], 0)
        paths = {n.get("path") for n in model.nodes}
        self.assertTrue("/transactions" in paths or "/health" in paths)

    def test_test_graph(self):
        model = GraphEngine().build_test_graph(
            ["tests/test_balance.py"], "pytest", PY_APP
        )
        self.assertEqual(model.graph_type, "test")
        self.assertTrue(any(n.get("kind") == "test" for n in model.nodes))

    def test_build_all_graph_types(self):
        graphs = GraphEngine().build_all(PY_APP)
        for key in GraphEngine.GRAPH_TYPES:
            self.assertIn(key, graphs)
            self.assertIn("nodes", graphs[key].to_dict())
            self.assertIn("edges", graphs[key].to_dict())
            self.assertIn("metadata", graphs[key].to_dict())

    def test_compose_and_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "graph_data.json")
            path = GraphEngine().write_graph_data(PY_APP, output_path=out)
            self.assertEqual(path, out)
            with open(out, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["engine"], "networkx")
            self.assertIn("graphs", data)
            self.assertIn("metadata", data)
            for gname in GraphEngine.GRAPH_TYPES:
                g = data["graphs"][gname]
                self.assertIn("nodes", g)
                self.assertIn("edges", g)
                self.assertIn("metadata", g)


if __name__ == "__main__":
    unittest.main(verbosity=2)
