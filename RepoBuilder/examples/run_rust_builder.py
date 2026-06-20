#!/usr/bin/env python3
"""Example: generate Rust logcount CLI for a repo workspace."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.rust_builder import RustBuilder  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 examples/run_rust_builder.py <repo_path>", file=sys.stderr)
        return 2

    repo = os.path.abspath(sys.argv[1])
    result = RustBuilder(workspace_root=os.path.join(ROOT, "workspace")).build(repo)
    print(f"Status: {result.status}")
    print(f"Project: {result.project_path}")
    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
