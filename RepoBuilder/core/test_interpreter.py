"""Parse test output and interpret failures."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TestCounts:
    passed: Optional[int] = None
    failed: Optional[int] = None
    skipped: Optional[int] = None
    total: Optional[int] = None


def parse_counts(framework: str, output: str) -> TestCounts:
    fw = framework.lower()
    counts = TestCounts()

    if "pytest" in fw:
        m = re.search(r"(\d+) passed", output)
        if m:
            counts.passed = int(m.group(1))
        m = re.search(r"(\d+) failed", output)
        if m:
            counts.failed = int(m.group(1))
        m = re.search(r"(\d+) skipped", output)
        if m:
            counts.skipped = int(m.group(1))

    elif fw in ("jest", "vitest", "mocha"):
        m = re.search(r"Tests:\s+(?:(\d+) failed,\s*)?(\d+) passed", output)
        if m:
            counts.failed = int(m.group(1) or 0)
            counts.passed = int(m.group(2))
        m = re.search(r"(\d+) passing", output)  # mocha style
        if m and counts.passed is None:
            counts.passed = int(m.group(1))
        m = re.search(r"(\d+) failing", output)
        if m:
            counts.failed = int(m.group(1))

    elif "cargo" in fw:
        m = re.search(r"(\d+) passed;\s*(\d+) failed", output)
        if m:
            counts.passed, counts.failed = int(m.group(1)), int(m.group(2))

    elif fw == "junit" or "maven" in fw or "gradle" in fw:
        m = re.search(r"Tests run:\s*(\d+),\s*Failures:\s*(\d+)", output)
        if m:
            total, failed = int(m.group(1)), int(m.group(2))
            counts.total = total
            counts.failed = failed
            counts.passed = total - failed

    if counts.passed is not None and counts.failed is not None:
        counts.total = counts.passed + counts.failed + (counts.skipped or 0)

    return counts


def interpret_failures(
    framework: str,
    output: str,
    exit_code: int,
    counts: TestCounts,
    timed_out: bool = False,
) -> str:
    if timed_out:
        return "Test run timed out — increase timeout or run a smaller subset."

    if exit_code == 0 and (counts.failed is None or counts.failed == 0):
        passed = counts.passed if counts.passed is not None else "all"
        return f"Tests completed successfully ({passed} passed)."

    if exit_code == 127 or "No such file or directory" in output:
        return "Test runner binary not found — install toolchain and dependencies first."

    parts: List[str] = []

    if counts.failed:
        parts.append(f"{counts.failed} test(s) failed.")

    fw = framework.lower()
    if "snapshot" in output.lower():
        parts.append("Snapshot mismatch — UI/component output changed vs stored snapshots.")
    if "Module not found" in output or "Cannot find module" in output:
        parts.append("Missing Node module — run npm install.")
    if "No module named" in output:
        parts.append("Missing Python package — run pip install / requirements.txt.")
    if "E   AssertionError" in output or "AssertionError" in output:
        parts.append("Assertion failures — expected values differ from actual.")
    if "SyntaxError" in output or "TS2307" in output or "TS" in output and "error TS" in output:
        parts.append("Syntax or type errors in source or tests.")
    if "cargo" in fw and "could not compile" in output.lower():
        parts.append("Rust compilation failed before tests could run.")
    if "junit" in fw and "BUILD FAILURE" in output:
        parts.append("Maven/Gradle build failed — see surefire reports in output.")

    if not parts:
        parts.append("Tests failed — inspect test_output.log for failing suites.")

    return " ".join(parts)
