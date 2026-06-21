#!/usr/bin/env python3
"""B3 — Test framework discovery and optional execution.

Detects the test framework(s) in a repo, the config file that drives them, the
relevant test files, and the exact command to run them. Use ``--run`` to execute
the primary detected command and print results with a short interpretation.

Coverage: pytest/unittest (Python), Jest/Vitest/Mocha (JS/TS), cargo test (Rust),
Maven/Gradle (Java/Kotlin), go test (Go).

Usage:
  python3 tests_detect.py <repo_path> [--json]
  python3 tests_detect.py <repo_path> --run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import detect  # noqa: E402


def file_exists(root, *names):
    for name in names:
        p = os.path.join(root, name)
        if os.path.exists(p):
            return name
    return None


def read(root, name):
    p = os.path.join(root, name)
    try:
        with open(p, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def find_test_files(root):
    """Return test files grouped by likely framework family."""
    py, js, rust, java, go = [], [], [], [], []
    for path, lang in detect.source_files(root):
        rel = detect.rel(path, root)
        base = os.path.basename(rel).lower()
        low = rel.lower()
        if lang == "python":
            if base.startswith("test_") or base.endswith("_test.py") or "/tests/" in "/" + low:
                py.append(rel)
        elif lang in ("javascript", "typescript"):
            if re.search(r"\.(test|spec)\.(js|jsx|ts|tsx)$", base) or "__tests__" in low:
                js.append(rel)
        elif lang == "rust":
            if "/tests/" in "/" + low or base == "tests.rs":
                rust.append(rel)
        elif lang in ("java", "kotlin"):
            if "test" in low and ("/test/" in "/" + low or base.endswith(("test.java", "tests.java", "test.kt"))):
                java.append(rel)
        elif lang == "go":
            if base.endswith("_test.go"):
                go.append(rel)
    return {"python": sorted(py), "js": sorted(js), "rust": sorted(rust),
            "java": sorted(java), "go": sorted(go)}


def detect_frameworks(root):
    frameworks = []
    tests = find_test_files(root)

    # --- Python ---
    pyproject = read(root, "pyproject.toml")
    setup_cfg = read(root, "setup.cfg")
    pytest_cfg = file_exists(root, "pytest.ini", "tox.ini", "conftest.py")
    # Also treat the suite as pytest if any test file imports/uses pytest.
    pytest_in_tests = any(
        "pytest" in "\n".join(detect.read_lines(os.path.join(root, tf)))
        for tf in tests["python"]
    )
    has_pytest = (
        "pytest" in pyproject or "pytest" in setup_cfg or pytest_cfg is not None
        or "[tool.pytest" in pyproject or pytest_in_tests
    )
    if tests["python"]:
        if has_pytest:
            if "pytest" in pyproject or "[tool.pytest" in pyproject:
                cfg = "pyproject.toml"
            elif pytest_cfg:
                cfg = pytest_cfg
            elif "pytest" in setup_cfg:
                cfg = "setup.cfg"
            else:
                cfg = None  # pytest in use but no dedicated config file
            frameworks.append({
                "framework": "pytest",
                "language": "python",
                "config_file": cfg,
                "test_files": tests["python"],
                "commands": ["python3 -m pytest -q"],
                "install": ["python3 -m pip install -r requirements.txt  # or: pip install pytest"],
            })
        else:
            frameworks.append({
                "framework": "unittest",
                "language": "python",
                "config_file": None,
                "test_files": tests["python"],
                "commands": ["python3 -m unittest discover"],
                "install": [],
            })

    # --- JS / TS ---
    pkg_raw = read(root, "package.json")
    if pkg_raw and tests["js"]:
        try:
            pkg = json.loads(pkg_raw)
        except ValueError:
            pkg = {}
        deps = {}
        deps.update(pkg.get("devDependencies", {}))
        deps.update(pkg.get("dependencies", {}))
        scripts = pkg.get("scripts", {})
        if "vitest" in deps:
            fw, cfg = "vitest", file_exists(root, "vitest.config.ts", "vitest.config.js", "vite.config.ts")
        elif "jest" in deps:
            fw, cfg = "jest", file_exists(root, "jest.config.js", "jest.config.ts", "jest.config.json")
        elif "mocha" in deps:
            fw, cfg = "mocha", file_exists(root, ".mocharc.json", ".mocharc.js")
        else:
            fw, cfg = "jest", None  # default assumption when a test script exists
        cmd = "npm test" if "test" in scripts else f"npx {fw}"
        frameworks.append({
            "framework": fw,
            "language": "javascript/typescript",
            "config_file": cfg or "package.json",
            "test_files": tests["js"],
            "commands": [cmd],
            "install": ["npm install"],
        })

    # --- Rust ---
    if file_exists(root, "Cargo.toml"):
        frameworks.append({
            "framework": "cargo test",
            "language": "rust",
            "config_file": "Cargo.toml",
            "test_files": tests["rust"] or ["(inline #[test] modules)"],
            "commands": ["cargo test"],
            "install": ["cargo build"],
        })

    # --- Java / Kotlin ---
    if file_exists(root, "pom.xml"):
        frameworks.append({
            "framework": "JUnit (Maven)",
            "language": "java",
            "config_file": "pom.xml",
            "test_files": tests["java"],
            "commands": ["mvn test"],
            "install": ["mvn -q compile"],
        })
    elif file_exists(root, "build.gradle", "build.gradle.kts"):
        frameworks.append({
            "framework": "JUnit (Gradle)",
            "language": "java/kotlin",
            "config_file": file_exists(root, "build.gradle", "build.gradle.kts"),
            "test_files": tests["java"],
            "commands": ["./gradlew test"],
            "install": [],
        })

    # --- Go ---
    if file_exists(root, "go.mod") and tests["go"]:
        frameworks.append({
            "framework": "go test",
            "language": "go",
            "config_file": "go.mod",
            "test_files": tests["go"],
            "commands": ["go test ./..."],
            "install": ["go mod download"],
        })

    return frameworks


def print_report(root, frameworks):
    if not frameworks:
        print("No test framework detected.")
        return
    print(f"Detected {len(frameworks)} test setup(s):\n")
    for fw in frameworks:
        print(f"## {fw['framework']}  ({fw['language']})")
        print(f"   config file : {fw['config_file']}")
        print(f"   test files  : {len(fw['test_files'])}")
        for tf in fw["test_files"][:15]:
            print(f"       - {tf}")
        if len(fw["test_files"]) > 15:
            print(f"       ... and {len(fw['test_files']) - 15} more")
        if fw["install"]:
            print(f"   install     : {' && '.join(fw['install'])}")
        print(f"   run command : {' && '.join(fw['commands'])}")
        print()


def parse_counts(framework: str, output: str) -> dict:
    fw = framework.lower()
    counts = {"passed": None, "failed": None, "skipped": None}

    if "pytest" in fw or fw == "unittest":
        m = re.search(r"(\d+) passed", output)
        if m:
            counts["passed"] = int(m.group(1))
        m = re.search(r"(\d+) failed", output)
        if m:
            counts["failed"] = int(m.group(1))
    elif fw in ("jest", "vitest", "mocha"):
        m = re.search(r"Tests:\s+(?:(\d+) failed,\s*)?(\d+) passed", output)
        if m:
            counts["failed"] = int(m.group(1) or 0)
            counts["passed"] = int(m.group(2))
    elif "cargo" in fw:
        m = re.search(r"(\d+) passed;\s*(\d+) failed", output)
        if m:
            counts["passed"], counts["failed"] = int(m.group(1)), int(m.group(2))
    elif "go test" in fw:
        m = re.search(r"ok\s+", output)
        if m and "FAIL" not in output:
            counts["passed"] = output.count("ok ")
    return counts


def interpret_run(framework: str, output: str, exit_code: int, counts: dict) -> str:
    if exit_code == 0 and (counts.get("failed") in (None, 0)):
        passed = counts.get("passed")
        return f"Tests completed successfully ({passed} passed)." if passed is not None else "Tests completed successfully."
    if exit_code == 127 or "command not found" in output.lower():
        return "Test runner not found — install dependencies first (see install commands above)."
    failed = counts.get("failed")
    if failed:
        return f"Tests failed ({failed} failure(s)). Review output below."
    return "Tests did not pass — review output below."


def run_framework(root: str, fw: dict, timeout: int = 300) -> dict:
    if not fw.get("commands"):
        return {"command": "", "exit_code": 0, "output": "", "interpretation": "No run command."}

    for install_cmd in fw.get("install") or []:
        subprocess.run(
            install_cmd,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    cmd = fw["commands"][0]
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        counts = parse_counts(fw["framework"], output)
        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "output": output,
            "counts": counts,
            "interpretation": interpret_run(fw["framework"], output, proc.returncode, counts),
        }
    except subprocess.TimeoutExpired:
        return {
            "command": cmd,
            "exit_code": 124,
            "output": f"Timed out after {timeout} seconds.",
            "counts": {},
            "interpretation": "Test run timed out.",
        }
    except OSError as exc:
        return {
            "command": cmd,
            "exit_code": 1,
            "output": str(exc),
            "counts": {},
            "interpretation": f"Could not run command: {exc}",
        }


def print_run_report(root: str, frameworks: list) -> int:
    if not frameworks:
        print("No test framework detected — nothing to run.")
        return 1

    primary = frameworks[0]
    print(f"Running primary framework: {primary['framework']}\n")
    result = run_framework(root, primary)
    print(f"$ {result['command']}")
    print(f"exit_code: {result['exit_code']}")
    print(f"interpretation: {result['interpretation']}")
    counts = result.get("counts") or {}
    if any(counts.get(k) is not None for k in ("passed", "failed", "skipped")):
        print(f"counts: {counts}")
    print("\n=== output ===")
    print(result["output"] or "(empty)")
    return 0 if result["exit_code"] == 0 else result["exit_code"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="B3 test framework discovery")
    ap.add_argument("repo")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--run",
        action="store_true",
        help="execute the primary detected test command and print results",
    )
    args = ap.parse_args(argv)
    if not os.path.isdir(args.repo):
        print(f"error: not a directory: {args.repo}", file=sys.stderr)
        return 2
    frameworks = detect_frameworks(args.repo)
    if args.run:
        print_report(args.repo, frameworks)
        return print_run_report(args.repo, frameworks)
    if args.json:
        print(json.dumps({"repo": os.path.abspath(args.repo), "frameworks": frameworks}, indent=2))
    else:
        print_report(args.repo, frameworks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
