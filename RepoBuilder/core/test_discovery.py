"""Discover test frameworks, config files, test files, and run commands."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from core.file_scanner import FileScanner

SUPPORTED = {"jest", "vitest", "mocha", "pytest", "junit", "cargo test"}


@dataclass
class TestFrameworkSetup:
    __test__ = False  # production dataclass, not a pytest test class
    framework: str
    language: str
    config_file: Optional[str]
    test_files: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    install: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "language": self.language,
            "config_file": self.config_file,
            "test_files": self.test_files,
            "commands": self.commands,
            "install": self.install,
        }


class TestDiscovery:
    """Detect Jest, Vitest, Mocha, pytest, JUnit, and cargo test in a repository."""

    __test__ = False  # production discovery class, not a pytest test class

    def __init__(self, scanner: Optional[FileScanner] = None) -> None:
        self.scanner = scanner or FileScanner()

    def discover(self, root: str) -> List[TestFrameworkSetup]:
        root = os.path.abspath(root)
        tests = self._find_test_files(root)
        setups: List[TestFrameworkSetup] = []

        py_setup = self._detect_python(root, tests["python"])
        if py_setup:
            setups.append(py_setup)

        js_setup = self._detect_js(root, tests["js"])
        if js_setup:
            setups.append(js_setup)

        if self._file_exists(root, "Cargo.toml"):
            setups.append(
                TestFrameworkSetup(
                    framework="cargo test",
                    language="rust",
                    config_file="Cargo.toml",
                    test_files=tests["rust"] or ["(inline #[test] modules)"],
                    commands=["cargo test"],
                    install=["cargo build"],
                )
            )

        junit = self._detect_junit(root, tests["java"])
        if junit:
            setups.append(junit)

        return setups

    def _find_test_files(self, root: str) -> dict:
        py, js, rust, java = [], [], [], []
        for abs_path, lang in self.scanner.iter_source_files(root):
            rel = os.path.relpath(abs_path, root)
            base = os.path.basename(rel).lower()
            low = rel.lower()
            if lang == "python":
                if base.startswith("test_") or base.endswith("_test.py") or "/tests/" in f"/{low}":
                    py.append(rel)
            elif lang in ("javascript", "typescript"):
                if re.search(r"\.(test|spec)\.(js|jsx|ts|tsx)$", base) or "__tests__" in low:
                    js.append(rel)
            elif lang == "rust":
                if "/tests/" in f"/{low}" or base == "tests.rs":
                    rust.append(rel)
            elif lang in ("java", "kotlin"):
                if "test" in low and (
                    "/test/" in f"/{low}"
                    or base.endswith(("test.java", "tests.java", "test.kt"))
                ):
                    java.append(rel)
        return {
            "python": sorted(py),
            "js": sorted(js),
            "rust": sorted(rust),
            "java": sorted(java),
        }

    def _detect_python(self, root: str, test_files: List[str]) -> Optional[TestFrameworkSetup]:
        if not test_files:
            return None
        pyproject = self._read(root, "pyproject.toml")
        setup_cfg = self._read(root, "setup.cfg")
        pytest_cfg = self._file_exists(root, "pytest.ini", "tox.ini", "conftest.py")
        pytest_in_tests = any(
            "pytest" in "\n".join(self.scanner.read_lines(os.path.join(root, tf)))
            for tf in test_files
        )
        has_pytest = (
            "pytest" in pyproject
            or "pytest" in setup_cfg
            or pytest_cfg is not None
            or "[tool.pytest" in pyproject
            or pytest_in_tests
        )
        if not has_pytest:
            return None

        if "pytest" in pyproject or "[tool.pytest" in pyproject:
            cfg = "pyproject.toml"
        elif pytest_cfg:
            cfg = pytest_cfg
        elif "pytest" in setup_cfg:
            cfg = "setup.cfg"
        else:
            cfg = None

        install = []
        if self._file_exists(root, "requirements.txt"):
            install.append("python3 -m pip install -r requirements.txt")
        install.append("python3 -m pip install pytest")

        return TestFrameworkSetup(
            framework="pytest",
            language="python",
            config_file=cfg,
            test_files=test_files,
            commands=["python3 -m pytest -q"],
            install=install,
        )

    def _detect_js(self, root: str, test_files: List[str]) -> Optional[TestFrameworkSetup]:
        pkg_raw = self._read(root, "package.json")
        if not pkg_raw or not test_files:
            return None
        try:
            pkg = json.loads(pkg_raw)
        except ValueError:
            return None

        deps = {}
        deps.update(pkg.get("devDependencies", {}))
        deps.update(pkg.get("dependencies", {}))
        scripts = pkg.get("scripts", {})

        if "vitest" in deps:
            fw = "vitest"
            cfg = self._file_exists(
                root, "vitest.config.ts", "vitest.config.js", "vite.config.ts"
            )
        elif "jest" in deps:
            fw = "jest"
            cfg = self._file_exists(
                root, "jest.config.js", "jest.config.ts", "jest.config.json"
            )
        elif "mocha" in deps:
            fw = "mocha"
            cfg = self._file_exists(root, ".mocharc.json", ".mocharc.js")
        elif "test" in scripts:
            fw = "jest"
            cfg = self._file_exists(
                root, "jest.config.js", "jest.config.ts", "jest.config.json"
            )
        else:
            return None

        cmd = "npm test" if "test" in scripts else f"npx {fw}"
        return TestFrameworkSetup(
            framework=fw,
            language="javascript/typescript",
            config_file=cfg or "package.json",
            test_files=test_files,
            commands=[cmd],
            install=["npm install"],
        )

    def _detect_junit(self, root: str, test_files: List[str]) -> Optional[TestFrameworkSetup]:
        if self._file_exists(root, "pom.xml"):
            return TestFrameworkSetup(
                framework="junit",
                language="java",
                config_file="pom.xml",
                test_files=test_files,
                commands=["mvn test"],
                install=["mvn -q compile"],
            )
        gradle = self._file_exists(root, "build.gradle", "build.gradle.kts")
        if gradle:
            return TestFrameworkSetup(
                framework="junit",
                language="java/kotlin",
                config_file=gradle,
                test_files=test_files,
                commands=["./gradlew test"],
                install=[],
            )
        return None

    @staticmethod
    def _file_exists(root: str, *names: str) -> Optional[str]:
        for name in names:
            if os.path.exists(os.path.join(root, name)):
                return name
        return None

    @staticmethod
    def _read(root: str, name: str) -> str:
        path = os.path.join(root, name)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""
