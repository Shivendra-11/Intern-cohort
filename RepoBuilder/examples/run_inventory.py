#!/usr/bin/env python3
"""Example: run B1 inventory agent on a repository.

Usage:
  python3 examples/run_inventory.py tests/fixtures/py_app
  python3 examples/run_inventory.py /path/to/your/repo
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.inventory_agent import InventoryAgent  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 examples/run_inventory.py <repo_path>", file=sys.stderr)
        return 2

    repo = os.path.abspath(sys.argv[1])
    agent = InventoryAgent(workspace_root=os.path.join(ROOT, "workspace"))
    result = agent.run(repo)

    out = os.path.join(ROOT, "workspace", result.repo_name, "B1_inventory")
    print()
    print("Generated:")
    print(f"  {out}/inventory.json")
    print(f"  {out}/inventory.md")
    print(f"  {out}/graph_data.json")
    print()
    print(f"Parser mode : {result.parser_mode}")
    print(f"Total items : {len(result.items)}")
    for cat, count in result.counts.items():
        if count:
            print(f"  {cat}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
