"""Scan repository metadata to inform A1 decomposition (repo-agnostic)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def scan_repo(repo_root: Path) -> dict[str, Any]:
    """Collect stack hints and top-level layout for planning."""
    meta: dict[str, Any] = {
        "repo_root": str(repo_root.resolve()),
        "stacks": [],
        "top_level_dirs": [],
        "top_level_files": [],
        "detected_patterns": [],
    }

    if not repo_root.is_dir():
        return meta

    for entry in sorted(repo_root.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            meta["top_level_dirs"].append(entry.name)
        else:
            meta["top_level_files"].append(entry.name)

    if (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
        meta["stacks"].append("python")
    if (repo_root / "package.json").exists():
        meta["stacks"].append("node")
    if (repo_root / "Cargo.toml").exists() or list(repo_root.glob("*/Cargo.toml")):
        meta["stacks"].append("rust")

    # Common fullstack layouts
    for name in meta["top_level_dirs"]:
        lower = name.lower()
        if any(k in lower for k in ("frontend", "client", "web", "ui")):
            meta["detected_patterns"].append("frontend_app")
        if any(k in lower for k in ("backend", "server", "api")):
            meta["detected_patterns"].append("backend_app")

    if (repo_root / "a3-polyglot" / "main.py").exists():
        meta["detected_patterns"].append("polyglot_fraud_pipeline")

    for sub in ("src", "app", "lib", "components", "server", "api", "tests", "ui", "docs"):
        if (repo_root / sub).exists():
            meta["detected_patterns"].append(f"dir:{sub}")

    pkg = repo_root / "package.json"
    if pkg.exists():
        try:
            meta["package_json"] = json.loads(pkg.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    return meta


# Default parallel lane archetypes (staff-engineer pattern)
DEFAULT_LANE_ARCHETYPES: list[dict[str, str]] = [
    {
        "name": "Fix bugs",
        "slug": "fix",
        "prefix": "fix",
        "goal": "Fix bugs and resolve defects in owned areas",
        "commit_prefix": "fix",
    },
    {
        "name": "Add features",
        "slug": "feature",
        "prefix": "feature",
        "goal": "Implement new features in owned areas",
        "commit_prefix": "feat",
    },
    {
        "name": "Improve tests & docs",
        "slug": "tests",
        "prefix": "chore",
        "goal": "Improve test coverage and documentation",
        "commit_prefix": "test",
    },
]


def suggest_lane_templates(
    task: str,
    meta: dict[str, Any],
    max_lanes: int,
    *,
    auto_generate: bool = True,
) -> list[dict[str, str]]:
    """Return lane templates based on task text, repo layout, and lane count."""
    task_lower = task.lower()
    patterns = meta.get("detected_patterns", [])
    templates: list[dict[str, str]] = []

    if auto_generate:
        templates = [
            {**arch, "goal": f"{arch['name']}: {task}"} for arch in DEFAULT_LANE_ARCHETYPES
        ]
    elif "polyglot_fraud_pipeline" in patterns or "fraud" in task_lower:
        templates = [
            {"name": "CSV Export", "slug": "export", "prefix": "feature", "goal": "Add export endpoint", "commit_prefix": "feat"},
            {"name": "Threshold Config", "slug": "thresholds", "prefix": "feature", "goal": "Add threshold API", "commit_prefix": "feat"},
            {"name": "Audit Log", "slug": "audit", "prefix": "feature", "goal": "Add audit logging", "commit_prefix": "feat"},
        ]
    else:
        templates = [
            {
                "name": "Primary",
                "slug": "primary",
                "prefix": "feature",
                "goal": task,
                "commit_prefix": "feat",
            }
        ]

    # Task-keyword overrides when auto_generate
    if auto_generate and max_lanes >= 2:
        if any(k in task_lower for k in ("bug", "fix", "defect")):
            templates[0]["goal"] = f"Fix bugs: {task}"
        if any(k in task_lower for k in ("feature", "add", "implement")):
            templates[1]["goal"] = f"Add features: {task}"
        if any(k in task_lower for k in ("test", "doc", "coverage")):
            templates[2]["goal"] = f"Improve tests/docs: {task}"

    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for t in templates:
        if t["slug"] not in seen:
            seen.add(t["slug"])
            unique.append(t)

    return unique[: max(1, min(max_lanes, len(unique) or 1))]
