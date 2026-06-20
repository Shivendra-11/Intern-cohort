#!/usr/bin/env python3
"""Tests for the repo-intelligence core framework (not B1–B6)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from core.file_scanner import FileScanner  # noqa: E402
from core.json_writer import JsonWriter, read_json  # noqa: E402
from core.report_generator import ReportGenerator, ReportSection  # noqa: E402
from core.shell_executor import ShellExecutor  # noqa: E402
from core.stack_detector import StackDetector  # noqa: E402

PY_APP = os.path.join(HERE, "fixtures", "py_app")
TS_APP = os.path.join(HERE, "fixtures", "ts_app")


class TestFileScanner(unittest.TestCase):
    def test_scan_python_fixture(self):
        result = FileScanner().scan(PY_APP)
        self.assertGreater(result.total_files, 0)
        langs = result.by_language
        self.assertIn("python", langs)
        rels = {f.relative_path for f in result.files}
        self.assertTrue(any("app/main.py" in r for r in rels))

    def test_scan_typescript_fixture(self):
        result = FileScanner().scan(TS_APP)
        langs = result.by_language
        self.assertTrue("typescript" in langs or "javascript" in langs)

    def test_config_detection(self):
        result = FileScanner().scan(PY_APP)
        configs = {f.relative_path for f in result.config_files}
        self.assertIn("pyproject.toml", configs)

    def test_invalid_root_raises(self):
        with self.assertRaises(ValueError):
            FileScanner().scan("/no/such/repo/path")


class TestStackDetector(unittest.TestCase):
    def test_detect_python(self):
        profile = StackDetector().detect(PY_APP)
        names = {s.name for s in profile.stacks}
        self.assertIn("python", names)
        self.assertEqual(profile.primary_stack, "python")
        self.assertEqual(profile.manifests.get("python"), "pyproject.toml")

    def test_detect_node(self):
        profile = StackDetector().detect(TS_APP)
        names = {s.name for s in profile.stacks}
        self.assertIn("node", names)
        self.assertEqual(profile.primary_stack, "node")
        self.assertEqual(profile.manifests.get("node"), "package.json")

    def test_detect_go_java_rust_in_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Go
            with open(os.path.join(tmp, "go.mod"), "w", encoding="utf-8") as fh:
                fh.write("module example.com/demo\n\ngo 1.21\n")
            os.makedirs(os.path.join(tmp, "cmd"))
            with open(os.path.join(tmp, "cmd", "main.go"), "w", encoding="utf-8") as fh:
                fh.write("package main\n\nfunc main() {}\n")

            # Rust (nested)
            rust_dir = os.path.join(tmp, "cli")
            os.makedirs(rust_dir)
            with open(os.path.join(rust_dir, "Cargo.toml"), "w", encoding="utf-8") as fh:
                fh.write('[package]\nname = "demo"\nversion = "0.1.0"\nedition = "2021"\n')
            os.makedirs(os.path.join(rust_dir, "src"))
            with open(os.path.join(rust_dir, "src", "main.rs"), "w", encoding="utf-8") as fh:
                fh.write("fn main() {}\n")

            # Java
            with open(os.path.join(tmp, "pom.xml"), "w", encoding="utf-8") as fh:
                fh.write("<project></project>\n")
            os.makedirs(os.path.join(tmp, "src", "main", "java"))
            with open(
                os.path.join(tmp, "src", "main", "java", "App.java"), "w", encoding="utf-8"
            ) as fh:
                fh.write("public class App {}\n")

            profile = StackDetector().detect(tmp)
            names = {s.name for s in profile.stacks}
            self.assertTrue({"go", "rust", "java"}.issubset(names))

    def test_to_dict_serializable(self):
        profile = StackDetector().detect(PY_APP)
        json.dumps(profile.to_dict())


class TestShellExecutor(unittest.TestCase):
    def test_argv_list_echo(self):
        result = ShellExecutor().run(["echo", "hello"])
        self.assertTrue(result.ok)
        self.assertIn("hello", result.stdout)

    def test_blocked_shell_command(self):
        with self.assertRaises(ValueError):
            ShellExecutor().run("rm -rf /", shell=True)

    def test_allowed_shell_prefix(self):
        result = ShellExecutor().run("echo safe-test", shell=True)
        self.assertTrue(result.ok)
        self.assertIn("safe-test", result.stdout)

    def test_missing_binary_exit_127(self):
        result = ShellExecutor().run(["/no/such/binary-xyz"])
        self.assertEqual(result.exit_code, 127)

    def test_to_dict(self):
        result = ShellExecutor().run(["echo", "x"])
        self.assertIn("command", result.to_dict())
        self.assertIn("ok", result.to_dict())


class TestJsonWriter(unittest.TestCase):
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nested", "data.json")
            writer = JsonWriter()
            writer.write(path, {"a": 1, "b": [2, 3]})
            self.assertTrue(os.path.isfile(path))
            loaded = read_json(path)
            self.assertEqual(loaded["a"], 1)
            self.assertEqual(loaded["b"], [2, 3])

    def test_atomic_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.json")
            writer = JsonWriter()
            writer.write(path, {"v": 1})
            writer.write(path, {"v": 2})
            self.assertEqual(read_json(path)["v"], 2)
            self.assertFalse(any(name.endswith(".tmp") for name in os.listdir(tmp)))

    def test_write_if_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.json")
            writer = JsonWriter()
            self.assertTrue(writer.write_if_changed(path, {"x": 1}))
            self.assertFalse(writer.write_if_changed(path, {"x": 1}))
            self.assertTrue(writer.write_if_changed(path, {"x": 2}))


class TestReportGenerator(unittest.TestCase):
    def test_generate_with_sections(self):
        gen = ReportGenerator()
        md = gen.generate(
            "Scan Report",
            sections=[
                ReportSection(title="Summary", body="Total files: 42"),
                ReportSection(
                    title="Stacks",
                    body=gen.table(
                        ["Stack", "Files"],
                        [["python", 10], ["node", 5]],
                    ),
                ),
            ],
            footer=gen.timestamp_footer("test"),
        )
        self.assertIn("# Scan Report", md)
        self.assertIn("## Summary", md)
        self.assertIn("| python | 10 |", md)
        self.assertIn("Generated by test", md)

    def test_section_from_dict(self):
        gen = ReportGenerator()
        section = gen.section_from_dict("Meta", {"repo": "/tmp/x", "count": 3})
        self.assertIn("**repo:**", section.body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
