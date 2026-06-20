#!/usr/bin/env python3
"""Generate a markdown onboarding report for a repository (B1 + B2 + B3).

Runs artifact inventory, API/route map, and test discovery, then writes a
single README-style markdown file instead of printing tables to the terminal.

Usage:
  python3 report.py <repo_path>
  python3 report.py <repo_path> --out REPO-ANALYSIS.md
  python3 report.py <repo_path> --run-tests
  python3 report.py <repo_path> --stdout   # print markdown instead of writing
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import endpoints  # noqa: E402
import inventory  # noqa: E402
import tests_detect  # noqa: E402

DEFAULT_OUT = "REPO-ANALYSIS.md"
NOISE_PATH_PARTS = ("/test/", "/tests/", "/__tests__/", "/docs/", "/examples/", "/example/")


def is_noise_route(file_path: str) -> bool:
    low = "/" + file_path.lower().replace("\\", "/")
    return any(part in low for part in NOISE_PATH_PARTS)


def repo_name(root: str) -> str:
    return os.path.basename(os.path.abspath(root).rstrip(os.sep)) or root


def section_inventory(result: dict, limit: int) -> list[str]:
    lines = ["## Artifact inventory (B1)", ""]
    total = sum(len(result[c]) for c in inventory.CATEGORIES)
    active = sum(1 for c in inventory.CATEGORIES if result[c])
    lines.append(f"**{total}** items across **{active}** categories.")
    lines.append("")

    for cat in inventory.CATEGORIES:
        items = result[cat]
        if not items:
            continue
        lines.append(f"### {cat} ({len(items)})")
        lines.append("")
        lines.append("| File | Name |")
        lines.append("|------|------|")
        for item in items[:limit]:
            lines.append(f"| `{item['file']}:{item['line']}` | {item['name']} |")
        if len(items) > limit:
            lines.append("")
            lines.append(f"*… and {len(items) - limit} more*")
        lines.append("")
    return lines


def section_endpoints(api: list, frontend: list) -> list[str]:
    lines = ["## API & routes (B2)", ""]

    prod_api = [e for e in api if not is_noise_route(e["file"])]
    noise_api = [e for e in api if is_noise_route(e["file"])]
    prod_fe = [e for e in frontend if not is_noise_route(e["file"])]
    noise_fe = [e for e in frontend if is_noise_route(e["file"])]

    lines.append(f"### API endpoints ({len(prod_api)} production, {len(noise_api)} in test/docs)")
    lines.append("")
    if prod_api:
        lines.append("| Method | Path | Handler | Location | Framework |")
        lines.append("|--------|------|---------|----------|-----------|")
        for e in prod_api:
            lines.append(
                f"| {e['method']} | `{e['path']}` | {e['handler']} "
                f"| `{e['file']}:{e['line']}` | {e['framework']} |"
            )
    else:
        lines.append("*(none detected in production paths)*")
    lines.append("")

    if noise_api:
        lines.append("<details>")
        lines.append(f"<summary>Test/fixture API routes ({len(noise_api)})</summary>")
        lines.append("")
        lines.append("| Method | Path | Location |")
        lines.append("|--------|------|----------|")
        for e in noise_api:
            lines.append(f"| {e['method']} | `{e['path']}` | `{e['file']}:{e['line']}` |")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append(f"### Frontend routes ({len(prod_fe)} production, {len(noise_fe)} in test/docs)")
    lines.append("")
    if prod_fe:
        lines.append("| Path | Location | Framework |")
        lines.append("|------|----------|-----------|")
        for e in prod_fe:
            lines.append(f"| `{e['path']}` | `{e['file']}:{e['line']}` | {e['framework']} |")
    else:
        lines.append("*(none detected in production paths)*")
    lines.append("")

    if noise_fe:
        lines.append("<details>")
        lines.append(f"<summary>Test/fixture frontend routes ({len(noise_fe)})</summary>")
        lines.append("")
        for e in noise_fe:
            lines.append(f"- `{e['path']}` — `{e['file']}:{e['line']}`")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    return lines


def section_tests(frameworks: list) -> list[str]:
    lines = ["## Test setup (B3)", ""]
    if not frameworks:
        lines.append("No test framework detected.")
        lines.append("")
        return lines

    for fw in frameworks:
        lines.append(f"### {fw['framework']} ({fw['language']})")
        lines.append("")
        lines.append(f"- **Config:** `{fw['config_file']}`")
        lines.append(f"- **Test files:** {len(fw['test_files'])}")
        if fw["test_files"]:
            lines.append("")
            for tf in fw["test_files"][:20]:
                lines.append(f"  - `{tf}`")
            if len(fw["test_files"]) > 20:
                lines.append(f"  - *… and {len(fw['test_files']) - 20} more*")
        lines.append("")
        if fw["install"]:
            lines.append(f"- **Install:** `{' && '.join(fw['install'])}`")
        lines.append(f"- **Run:** `{' && '.join(fw['commands'])}`")
        lines.append("")
    return lines


def run_test_command(root: str, fw: dict) -> tuple[str, str, int]:
    """Run the first test command for a framework; return (cmd, output, exit_code)."""
    if not fw["commands"]:
        return "", "", 0
    cmd = fw["commands"][0]
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return cmd, output.strip(), proc.returncode
    except subprocess.TimeoutExpired:
        return cmd, "Timed out after 300 seconds.", 124
    except OSError as exc:
        return cmd, f"Could not run command: {exc}", 1


def section_test_run(root: str, frameworks: list, run_tests: bool) -> list[str]:
    lines = ["## Test execution", ""]
    if not run_tests:
        lines.append(
            "*Tests were not executed. Re-run with `--run-tests` to append live output.*"
        )
        lines.append("")
        return lines

    if not frameworks:
        lines.append("No test framework to run.")
        lines.append("")
        return lines

    for fw in frameworks:
        if not fw["commands"]:
            continue
        cmd, output, code = run_test_command(root, fw)
        lines.append(f"### {fw['framework']}")
        lines.append("")
        lines.append("```bash")
        lines.append(f"cd {os.path.abspath(root)}")
        if fw["install"]:
            lines.append(" && ".join(fw["install"]))
        lines.append(cmd)
        lines.append("```")
        lines.append("")
        lines.append(f"**Exit code:** {code}")
        lines.append("")
        lines.append("```")
        lines.append(output or "(no output)")
        lines.append("```")
        lines.append("")
    return lines


def build_report(root: str, limit: int, run_tests: bool) -> str:
    inv = inventory.build_inventory(root)
    api, frontend = endpoints.build_routes(root)
    frameworks = tests_detect.detect_frameworks(root)

    lines = [
        f"# Repository analysis — {repo_name(root)}",
        "",
        f"Generated by repo-builder `report.py` on "
        f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        f"**Repository path:** `{os.path.abspath(root)}`",
        "",
        "> Best-effort regex heuristics — verify suspicious counts by reading source files.",
        "",
        "---",
        "",
    ]
    lines.extend(section_inventory(inv, limit))
    lines.append("---")
    lines.append("")
    lines.extend(section_endpoints(api, frontend))
    lines.append("---")
    lines.append("")
    lines.extend(section_tests(frameworks))
    lines.append("---")
    lines.append("")
    lines.extend(section_test_run(root, frameworks, run_tests))
    lines.append("---")
    lines.append("")
    lines.append("## Regenerate this report")
    lines.append("")
    lines.append("```bash")
    lines.append(f"python3 ~/.claude/repo-builder/scripts/report.py {os.path.abspath(root)}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Generate a markdown repo onboarding report (B1+B2+B3)"
    )
    ap.add_argument("repo", help="path to the repository to analyze")
    ap.add_argument(
        "--out",
        default=DEFAULT_OUT,
        help=f"output markdown file inside the repo (default: {DEFAULT_OUT})",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=25,
        help="max inventory items per category (default: 25)",
    )
    ap.add_argument(
        "--run-tests",
        action="store_true",
        help="execute detected test commands and append output",
    )
    ap.add_argument(
        "--stdout",
        action="store_true",
        help="print markdown to stdout instead of writing a file",
    )
    args = ap.parse_args(argv)

    if not os.path.isdir(args.repo):
        print(f"error: not a directory: {args.repo}", file=sys.stderr)
        return 2

    markdown = build_report(args.repo, args.limit, args.run_tests)

    if args.stdout:
        print(markdown)
        return 0

    out_path = args.out
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.path.abspath(args.repo), out_path)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(markdown)

    print(f"Wrote report to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
