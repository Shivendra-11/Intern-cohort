"""Remove workspace outputs."""
from __future__ import annotations

import argparse
import shutil
import sys

from cli.paths import STATE_DIR, WORKSPACE_ROOT


def run_clean(repo_name: str | None = None) -> int:
    if not WORKSPACE_ROOT.is_dir():
        print("workspace/ does not exist — nothing to clean.")
        return 0

    if repo_name:
        target = WORKSPACE_ROOT / repo_name
        if not target.is_dir():
            print(f"not found: {target}", file=sys.stderr)
            return 1
        shutil.rmtree(target)
        print(f"removed {target}")
        return 0

    removed = 0
    for entry in sorted(WORKSPACE_ROOT.iterdir()):
        if entry.name == ".repo-intelligence":
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
            print(f"removed {entry}")
            removed += 1

    if STATE_DIR.is_dir():
        shutil.rmtree(STATE_DIR)
        print(f"removed {STATE_DIR}")

    if removed == 0:
        print("workspace is already empty.")
    else:
        print(f"cleaned {removed} repo workspace(s).")
    return 0


def main_clean(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Remove workspace analysis outputs")
    ap.add_argument("repo_name", nargs="?", help="specific repo name (default: all)")
    args = ap.parse_args(argv)
    return run_clean(args.repo_name)
