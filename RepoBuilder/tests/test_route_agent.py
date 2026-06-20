#!/usr/bin/env python3
"""Tests for core.route_agent (B2)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.route_agent import RouteAgent, RouteRecord  # noqa: E402
from core.route_scanners import scan_repo  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
TS_APP = os.path.join(HERE, "fixtures", "ts_app")


class TestRouteAgent(unittest.TestCase):
    def test_py_app_fastapi_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = RouteAgent(workspace_root=os.path.join(tmp, "ws")).run(PY_APP)
            out = os.path.join(tmp, "ws", "py_app", "B2_routes")
            self.assertTrue(os.path.isfile(os.path.join(out, "routes.json")))
            self.assertTrue(os.path.isfile(os.path.join(out, "routes.md")))
            self.assertTrue(os.path.isfile(os.path.join(out, "route_graph.json")))

            paths = {(r.method, r.path) for r in result.backend}
            self.assertIn(("POST", "/transactions"), paths)
            self.assertIn(("GET", "/transactions"), paths)
            self.assertIn(("GET", "/balance"), paths)

    def test_ts_app_express_and_react(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = RouteAgent(workspace_root=os.path.join(tmp, "ws")).run(TS_APP)
            backend_paths = {(r.method, r.path) for r in result.backend}
            self.assertIn(("GET", "/health"), backend_paths)
            self.assertIn(("POST", "/transactions"), backend_paths)

            fe_paths = {r.path for r in result.frontend}
            self.assertIn("/transactions", fe_paths)

    def test_route_record_has_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = RouteAgent(workspace_root=os.path.join(tmp, "ws")).run(PY_APP)
            for r in result.all_routes:
                self.assertTrue(r.file)
                self.assertTrue(r.method)
                self.assertTrue(r.path.startswith("/"))

    def test_routes_json_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "ws", "py_app", "B2_routes")
            RouteAgent(workspace_root=os.path.join(tmp, "ws")).run(PY_APP)
            with open(os.path.join(out, "routes.json"), encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertIn("backend", data)
            self.assertIn("frontend", data)
            self.assertIn("routes", data)
            item = data["backend"][0]
            self.assertIn("method", item)
            self.assertIn("path", item)
            self.assertIn("file", item)

    def test_route_graph_structure(self):
        routes = [
            RouteRecord("GET", "/a", "src/a.py", 1, "Express", "backend"),
            RouteRecord("POST", "/a/b", "src/a.py", 2, "Express", "backend"),
        ]
        graph = RouteAgent.build_route_graph(routes)
        self.assertEqual(graph["node_count"], 2)
        self.assertGreaterEqual(graph["edge_count"], 1)

    def test_create_browser_router_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "src", "router.jsx")
            os.makedirs(os.path.dirname(src))
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(
                    "import { createBrowserRouter } from 'react-router-dom';\n"
                    "export const router = createBrowserRouter([\n"
                    "  { path: '/dashboard', element: <Dash /> },\n"
                    "]);\n"
                )
            _, frontend = scan_repo(tmp)
            paths = {r.path for r in frontend}
            self.assertIn("/dashboard", paths)
            frameworks = {r.framework for r in frontend}
            self.assertIn("createBrowserRouter", frameworks)

    def test_markdown_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = RouteAgent(workspace_root=os.path.join(tmp, "ws")).run(PY_APP)
            md = RouteAgent().render_markdown(result)
            self.assertIn("# Routes — py_app", md)
            self.assertIn("## Backend Routes", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
