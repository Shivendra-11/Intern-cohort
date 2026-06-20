"""List analyzed repositories in workspace."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from cli.paths import WORKSPACE_ROOT
from cli.state import load_state


def run_list() -> int:
    if not WORKSPACE_ROOT.is_dir():
        print("No workspace yet. Run: repo-intelligence analyze <repo>")
        return 0

    last = load_state()
    rows = []

    for entry in sorted(WORKSPACE_ROOT.iterdir()):
        if entry.name.startswith(".") or not entry.is_dir():
            continue
        dashboard = entry / "dashboard_data.json"
        status = "partial"
        repo_name = entry.name
        generated_at = ""

        if dashboard.is_file():
            try:
                with open(dashboard, encoding="utf-8") as fh:
                    data = json.load(fh)
                summary = data.get("summary", {})
                pipelines = summary.get("pipelines", {})
                complete = all(
                    pipelines.get(k) == "complete"
                    for k in ("B1_inventory", "B2_routes", "B3_tests", "graphs")
                )
                status = "complete" if complete else "partial"
                repo_name = data.get("repo_name", entry.name)
                generated_at = data.get("generated_at", "")[:19]
            except (OSError, json.JSONDecodeError):
                status = "invalid"

        marker = " *" if last and last.repo_name == entry.name else ""
        rows.append((entry.name, status, generated_at, marker))

    if not rows:
        print("No analyzed repos in workspace/.")
        return 0

    print(f"{'REPO':<20} {'STATUS':<10} {'UPDATED':<20}")
    print("-" * 52)
    for name, status, updated, marker in rows:
        print(f"{name:<20} {status:<10} {updated:<20}{marker}")

    if last:
        print("")
        print(f"* last served: {last.repo_name} → {last.dashboard_path}")
    return 0


def main_list(argv=None) -> int:
    return run_list()
