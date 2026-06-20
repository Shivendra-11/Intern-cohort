#!/usr/bin/env python3
"""Example: build dashboard_data.json from workspace artifacts."""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.dashboard_data_builder import DashboardDataBuilder  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 examples/run_dashboard_data_builder.py <repo_path>", file=sys.stderr)
        return 2

    repo = os.path.abspath(sys.argv[1])
    result = DashboardDataBuilder(workspace_root=os.path.join(ROOT, "workspace")).build(repo)

    print(f"Wrote: {result.output_path}")
    print()
    print("--- summary ---")
    print(json.dumps(result.payload["summary"], indent=2))
    print()
    print("--- top-level keys ---")
    for key in result.payload:
        if key in ("inventory", "routes", "tests", "graphs"):
            val = result.payload[key]
            print(f"  {key}: {'loaded' if val else 'missing'}")
        elif key == "generated_projects":
            print(f"  generated_projects: {list(result.payload[key].keys())}")
        else:
            print(f"  {key}: {type(result.payload[key]).__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
