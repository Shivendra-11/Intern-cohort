#!/usr/bin/env python3
"""Example: run B2 route agent on a repository."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.route_agent import RouteAgent  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 examples/run_routes.py <repo_path>", file=sys.stderr)
        return 2

    repo = os.path.abspath(sys.argv[1])
    agent = RouteAgent(workspace_root=os.path.join(ROOT, "workspace"))
    result = agent.run(repo)

    out = os.path.join(ROOT, "workspace", result.repo_name, "B2_routes")
    print()
    print("Generated:")
    print(f"  {out}/routes.json")
    print(f"  {out}/routes.md")
    print(f"  {out}/route_graph.json")
    print()
    print(f"Backend  : {len(result.backend)}")
    print(f"Frontend : {len(result.frontend)}")
    for r in result.production_backend[:5]:
        print(f"  {r.method:6} {r.path:25} {r.file} [{r.framework}]")
    for r in result.production_frontend[:5]:
        print(f"  {r.method:6} {r.path:25} {r.file} [{r.framework}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
