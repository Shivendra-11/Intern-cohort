#!/usr/bin/env python3
"""Repo Intelligence CLI — analyze repos and serve the dashboard."""
from __future__ import annotations

import argparse
import sys

from cli.analyze import run_analyze
from cli.clean import run_clean
from cli.list_cmd import run_list
from cli.paths import UI_URL
from cli.serve import run_serve
from cli.state import PlatformState, save_state


def _cmd_analyze(args: argparse.Namespace) -> int:
    serve = not args.no_serve
    try:
        result = run_analyze(
            args.repo,
            run_tests=not args.skip_tests,
            builder_proof=args.proof,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not result.ok and not serve:
        return 1

    if not serve:
        print("Dashboard data ready. Run: repo-intelligence serve")
        print(f"  → {UI_URL}")
        return 0 if result.ok else 1

    state = PlatformState(
        repo_path=result.repo_path,
        repo_name=result.repo_name,
        dashboard_path=result.dashboard_path,
        workspace_dir=result.workspace_dir,
    )
    save_state(state)
    code = run_serve(open_browser=args.open, state=state)
    return code if result.ok else 1


def _cmd_serve(args: argparse.Namespace) -> int:
    return run_serve(open_browser=args.open)


def _cmd_clean(args: argparse.Namespace) -> int:
    return run_clean(args.repo_name)


def _cmd_list(_args: argparse.Namespace) -> int:
    return run_list()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="repo-intelligence",
        description="Analyze repositories and serve the Repo Intelligence dashboard.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser(
        "analyze",
        help="Run B1–B6 pipeline, build dashboard_data.json, start servers",
    )
    p_analyze.add_argument("repo", help="path to repository to analyze")
    p_analyze.add_argument(
        "--open",
        action="store_true",
        help="open browser at http://localhost:3000 after startup",
    )
    p_analyze.add_argument(
        "--no-serve",
        action="store_true",
        help="generate outputs only; do not start API/UI servers",
    )
    p_analyze.add_argument(
        "--skip-tests",
        action="store_true",
        help="B3 discovery only; do not execute tests",
    )
    p_analyze.add_argument(
        "--proof",
        action="store_true",
        help="run full proof (tests/build) for B4–B6 greenfield projects",
    )
    p_analyze.set_defaults(func=_cmd_analyze)

    p_serve = sub.add_parser("serve", help="Start API + dashboard for last analyze")
    p_serve.add_argument("--open", action="store_true", help="open browser")
    p_serve.set_defaults(func=_cmd_serve)

    p_clean = sub.add_parser("clean", help="Remove workspace outputs")
    p_clean.add_argument("repo_name", nargs="?", help="repo name (default: all)")
    p_clean.set_defaults(func=_cmd_clean)

    p_list = sub.add_parser("list", help="List analyzed repos in workspace")
    p_list.set_defaults(func=_cmd_list)

    return ap


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
