"""Tests for canonical route deduplication."""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.route_dedupe import dedupe_backend_routes  # noqa: E402
from core.route_scanners import AstRoute  # noqa: E402

TS_APP = os.path.join(HERE, "fixtures", "ts_app")


class TestRouteDedupe(unittest.TestCase):
    def test_collapsing_duplicate_post_transactions(self):
        routes = [
            AstRoute("POST", "/transactions", 5, "Express", "src/server.js", "(inline)"),
            AstRoute("POST", "/transactions", 10, "NestJS", "src/transactions/transactions.controller.ts", "create"),
        ]
        deduped = dedupe_backend_routes(routes)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].framework, "NestJS")
        self.assertEqual(deduped[0].handler, "create")

    def test_ts_fixture_has_three_canonical_api_routes(self):
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import endpoints  # noqa: E402

        api, _ = endpoints.build_routes(TS_APP)
        keys = {(e["method"], e["path"]) for e in api}
        self.assertEqual(len(api), 3)
        self.assertIn(("GET", "/health"), keys)
        self.assertIn(("POST", "/transactions"), keys)
        self.assertIn(("GET", "/transactions"), keys)


if __name__ == "__main__":
    unittest.main(verbosity=2)
