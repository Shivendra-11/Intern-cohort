#!/usr/bin/env python3
"""Reproducible proof: run the read-side eval tasks against a *real, unfamiliar*
third-party repository (not an author-authored fixture).

This closes the eval doc's core framing — "in *this* repo / an unfamiliar module" —
by pointing the deterministic, no-API scanners at an external open-source codebase
and machine-capturing the per-task wall-clock (analogous to DevOps `duration_seconds`).

Tasks exercised, all deterministic (AST / static analysis — no model calls):

  B1 inventory   + B2 routes + B3 test discovery   via `repo-intelligence analyze`
  I1 ER diagram  (scan_entities → infer_relationships → build_er_mermaid)
  I2 flow trace  (find_entry_points → scan_flow_steps → build_sequence_mermaid)

Usage:
    python run_external_proof.py [REPO_PATH] [BACKEND_SUBDIR]

Defaults match the README's clone instructions:
    REPO_PATH      = /tmp/ext-eval-repo
    BACKEND_SUBDIR = backend     (where the Python DB models live)

Re-running it on the same pinned commit regenerates byte-identical reports.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from polyglot_eval import repo_scanner as rs

HERE = Path(__file__).resolve().parent
REPORTS = HERE / "reports"
REPORTS.mkdir(exist_ok=True)


def _timed(label: str, fn):
    t0 = time.perf_counter()
    out = fn()
    dt = time.perf_counter() - t0
    print(f"  [{label}] {dt*1000:.0f} ms")
    return out, dt


def write_i1(repo: Path) -> float:
    print("I1 — ER diagram")
    t0 = time.perf_counter()
    (entities, _) = _timed("scan_entities", lambda: rs.scan_entities(repo))
    (rels, _) = _timed("infer_relationships", lambda: rs.infer_relationships(entities))
    (mermaid, _) = _timed("build_er_mermaid", lambda: rs.build_er_mermaid(entities, rels))

    lines = [
        "# I1 — ER diagram (external repo)",
        "",
        f"Source: `{repo}` — scanned with `polyglot_eval.repo_scanner` (AST, no model calls).",
        "",
        f"**{len(entities)} entities · {len(rels)} inferred relationships.**",
        "",
        "## Entities (with source citations)",
        "",
        "| Entity | Source file | Line | Columns |",
        "| --- | --- | --- | --- |",
    ]
    for e in entities:
        cols = ", ".join(
            f"{c['name']}:{c['type']}"
            + ("(PK)" if c.get("isPK") else "")
            + ("(FK)" if c.get("isFK") else "")
            for c in e.get("columns", [])
        )
        # Escape pipes so union types like `str | None` don't split the table column.
        cols = cols.replace("|", "\\|")
        lines.append(
            f"| `{e['name']}` | {e['sourceFile']} | {e['sourceLine']} | {cols or '—'} |"
        )

    lines += ["", "## Inferred relationships", ""]
    if rels:
        lines += ["| From | To | Basis |", "| --- | --- | --- |"]
        for r in rels:
            lines.append(
                f"| `{r.get('from')}` | `{r.get('to')}` | {r.get('via') or r.get('basis') or 'FK/column name'} |"
            )
    else:
        lines.append("_No cross-entity relationships inferred._")

    lines += ["", "## Mermaid ER diagram", "", "```mermaid", mermaid, "```", ""]
    (REPORTS / "I1_er_diagram.md").write_text("\n".join(lines))
    dt = time.perf_counter() - t0
    return dt


def write_i2(repo: Path) -> float:
    print("I2 — flow trace")
    t0 = time.perf_counter()
    (eps, _) = _timed("find_entry_points", lambda: rs.find_entry_points(repo))
    (routes, _) = _timed("grep_routes", lambda: rs.grep_routes(repo))
    (steps, _) = _timed("scan_flow_steps", lambda: rs.scan_flow_steps(repo))
    (seq, _) = _timed(
        "build_sequence_mermaid", lambda: rs.build_sequence_mermaid(repo, steps, routes)
    )

    lines = [
        "# I2 — End-to-end flow trace (external repo)",
        "",
        f"Source: `{repo}` — scanned with `polyglot_eval.repo_scanner` (AST, no model calls).",
        "",
        f"**{len(eps)} entry point(s) · {len(routes)} routes · {len(steps)} flow steps.**",
        "",
        "## Entry points",
        "",
        "| File | Function | Line |",
        "| --- | --- | --- |",
    ]
    for e in eps:
        lines.append(f"| {e.get('file')} | `{e.get('function')}` | {e.get('line')} |")

    lines += ["", "## Routes (externally exposed)", "", ", ".join(f"`{r}`" for r in routes), ""]

    lines += ["## Step-by-step path", "", "| # | File | Function | Line | I/O |", "| --- | --- | --- | --- | --- |"]
    for s in steps:
        lines.append(
            f"| {s.get('index')} | {s.get('file')} | `{s.get('function')}` | {s.get('line')} | {s.get('ioType','')} |"
        )

    lines += ["", "## Sequence diagram", "", "```mermaid", seq, "```", ""]
    (REPORTS / "I2_flow_trace.md").write_text("\n".join(lines))
    dt = time.perf_counter() - t0
    return dt


def run_b_pipeline(repo: Path) -> tuple[float, Path]:
    """B1/B2/B3 via the RepoBuilder CLI; returns wall-clock + workspace dir."""
    print("B1/B2/B3 — repo-intelligence analyze")
    t0 = time.perf_counter()
    subprocess.run(
        ["repo-intelligence", "analyze", str(repo), "--no-serve", "--skip-tests"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    dt = time.perf_counter() - t0
    print(f"  [analyze] {dt:.1f} s")
    # Locate the workspace the CLI wrote to.
    ws = Path(__file__).resolve().parents[2] / "RepoBuilder" / "workspace" / repo.name
    return dt, ws


def main() -> int:
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/ext-eval-repo")
    backend = sys.argv[2] if len(sys.argv) > 2 else "backend"
    if not repo_root.exists():
        print(f"ERROR: {repo_root} not found. Clone it first (see README.md).", file=sys.stderr)
        return 2

    backend_path = repo_root / backend if (repo_root / backend).exists() else repo_root
    print(f"External repo: {repo_root}")
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        commit = "unknown"
    print(f"Pinned commit: {commit}\n")

    timings: dict[str, float] = {}
    b_dt, ws = run_b_pipeline(repo_root)
    timings["B1+B2+B3 (analyze)"] = b_dt
    # Copy the B-track reports next to the I-track ones.
    for sub, name in [
        ("B1_inventory/inventory.md", "B1_inventory.md"),
        ("B2_routes/routes.md", "B2_routes.md"),
        ("B3_tests/tests.md", "B3_tests.md"),
    ]:
        src = ws / sub
        if src.exists():
            (REPORTS / name).write_text(src.read_text())

    timings["I1 ER diagram"] = write_i1(backend_path)
    timings["I2 flow trace"] = write_i2(backend_path)

    summary = {
        "external_repo": str(repo_root),
        "pinned_commit": commit,
        "backend_scanned": str(backend_path),
        "wall_clock_seconds": {k: round(v, 3) for k, v in timings.items()},
        "deterministic": True,
        "model_calls": 0,
    }
    (REPORTS / "timings.json").write_text(json.dumps(summary, indent=2))
    print("\nWall-clock (machine-captured):")
    for k, v in timings.items():
        print(f"  {k:24} {v:.3f} s")
    print(f"\nReports written to {REPORTS}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
