#!/usr/bin/env python3
"""Self-tests for the repo-builder scanners.

Runs each scanner against the fixture mini-repos under tests/fixtures/ and
asserts the key artifacts/endpoints/frameworks are detected. Stdlib unittest so
it runs anywhere with no dependencies:

    python3 tests/test_scanners.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import endpoints  # noqa: E402
import inventory  # noqa: E402
import report  # noqa: E402
import tests_detect  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
TS_APP = os.path.join(HERE, "fixtures", "ts_app")


def names(items):
    return {i["name"] for i in items}


def paths(items):
    return {(i["method"], i["path"]) for i in items}


class TestInventory(unittest.TestCase):
    def test_python_artifacts(self):
        inv = inventory.build_inventory(PY_APP)
        self.assertIn("LedgerService", names(inv["services"]))
        self.assertIn("TransactionIn", names(inv["models"]))
        self.assertIn("nightly_rollup", names(inv["jobs"]))
        self.assertTrue(any("pyproject.toml" == i["name"] for i in inv["configs"]))

    def test_typescript_artifacts(self):
        inv = inventory.build_inventory(TS_APP)
        self.assertIn("TransactionsController", names(inv["controllers"]))
        self.assertIn("TransactionsService", names(inv["services"]))
        self.assertIn("TransactionsRepository", names(inv["repositories"]))
        self.assertIn("Transaction", names(inv["interfaces"]))


class TestEndpoints(unittest.TestCase):
    def test_fastapi_routes(self):
        api, _ = endpoints.build_routes(PY_APP)
        ps = paths(api)
        self.assertIn(("POST", "/transactions"), ps)
        self.assertIn(("GET", "/transactions"), ps)
        self.assertIn(("GET", "/balance"), ps)

    def test_express_and_nest_routes(self):
        api, frontend = endpoints.build_routes(TS_APP)
        ps = paths(api)
        self.assertEqual(len(api), 3, "canonical dedupe should collapse duplicate POST /transactions")
        self.assertIn(("GET", "/health"), ps)          # express
        self.assertIn(("POST", "/transactions"), ps)   # nest preferred over express inline
        self.assertIn(("GET", "/transactions"), ps)    # nest controller prefix joined
        fp = {e["path"] for e in frontend}
        self.assertIn("/transactions", fp)             # react router


class TestReport(unittest.TestCase):
    def test_generates_markdown_with_all_sections(self):
        md = report.build_report(PY_APP, limit=10, run_tests=False)
        self.assertIn("# Repository analysis — py_app", md)
        self.assertIn("## Artifact inventory (B1)", md)
        self.assertIn("LedgerService", md)
        self.assertIn("## API & routes (B2)", md)
        self.assertIn("/transactions", md)
        self.assertIn("## Test setup (B3)", md)
        self.assertIn("pytest", md)

    def test_writes_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "REPO-ANALYSIS.md")
            code = report.main([PY_APP, "--out", out])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(out))
            with open(out, encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("Repository analysis", content)


class TestTestsDetect(unittest.TestCase):
    def test_python_pytest(self):
        fws = tests_detect.detect_frameworks(PY_APP)
        py = [f for f in fws if f["framework"] == "pytest"]
        self.assertTrue(py, "expected pytest to be detected")
        self.assertEqual(py[0]["config_file"], "pyproject.toml")
        self.assertTrue(any("test_balance.py" in t for t in py[0]["test_files"]))

    def test_js_jest(self):
        fws = tests_detect.detect_frameworks(TS_APP)
        js = [f for f in fws if f["framework"] == "jest"]
        self.assertTrue(js, "expected jest to be detected")
        self.assertEqual(js[0]["commands"], ["npm test"])

    def test_run_flag_executes_py_app(self):
        result_code = tests_detect.main([PY_APP, "--run"])
        self.assertEqual(result_code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
