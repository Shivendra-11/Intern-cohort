#!/usr/bin/env python3
"""Example: run B3 test agent on a repository."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.test_agent import TestAgent  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 examples/run_tests.py <repo_path>", file=sys.stderr)
        return 2

    repo = os.path.abspath(sys.argv[1])
    agent = TestAgent(workspace_root=os.path.join(ROOT, "workspace"))
    result = agent.run(repo)

    out = os.path.join(ROOT, "workspace", result.repo_name, "B3_tests")
    print()
    print("Generated:")
    print(f"  {out}/tests.json")
    print(f"  {out}/tests.md")
    print(f"  {out}/test_output.log")
    print()
    if result.primary:
        print(f"Framework : {result.primary.framework}")
        print(f"Config    : {result.primary.config_file}")
        print(f"Command   : {result.primary.commands[0]}")
    print(f"Status    : {result.execution.status}")
    print(f"Passed    : {result.execution.passed}")
    print(f"Failed    : {result.execution.failed}")
    print(f"Interpret : {result.execution.interpretation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
