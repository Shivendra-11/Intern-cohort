"""Phase 2 — deep repository analysis for lane decomposition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from parallelops.repo_scanner import scan_repo


def analyze_repository(repo_root: Path) -> dict[str, Any]:
    """Understand structure, stacks, tests, and parallelizable areas."""
    meta = scan_repo(repo_root)
    analysis: dict[str, Any] = {
        **meta,
        "package_managers": [],
        "languages": [],
        "build_systems": [],
        "test_frameworks": [],
        "parallelizable_areas": [],
        "ownership_hints": {},
    }

    if (repo_root / "package.json").exists():
        analysis["package_managers"].append("npm")
        analysis["languages"].append("javascript")
        analysis["build_systems"].append("npm scripts")
        pkg = meta.get("package_json") or {}
        scripts = pkg.get("scripts") or {}
        if "test" in scripts:
            analysis["test_frameworks"].append("npm test")
        if "lint" in scripts:
            analysis["test_frameworks"].append("npm run lint")
        if "build" in scripts:
            analysis["test_frameworks"].append("npm run build")

    if (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
        analysis["package_managers"].append("pip")
        analysis["languages"].append("python")
        if (repo_root / "pytest.ini").exists() or list(repo_root.glob("**/test_*.py")):
            analysis["test_frameworks"].append("pytest")
        if (repo_root / "setup.py").exists():
            analysis["build_systems"].append("setup.py")

    if (repo_root / "Cargo.toml").exists() or list(repo_root.glob("*/Cargo.toml")):
        analysis["package_managers"].append("cargo")
        analysis["languages"].append("rust")
        analysis["test_frameworks"].append("cargo test")

    if (repo_root / "go.mod").exists():
        analysis["package_managers"].append("go modules")
        analysis["languages"].append("go")
        analysis["test_frameworks"].append("go test")

    dirs = meta.get("top_level_dirs", [])
    for d in dirs:
        lower = d.lower()
        if any(k in lower for k in ("frontend", "client", "web", "ui")):
            analysis["ownership_hints"]["ui"] = analysis["ownership_hints"].get("ui", []) + [f"{d}/"]
            analysis["parallelizable_areas"].append({"area": "ui", "paths": [f"{d}/"]})
        if any(k in lower for k in ("backend", "server", "api")):
            analysis["ownership_hints"]["api"] = analysis["ownership_hints"].get("api", []) + [f"{d}/"]
            analysis["parallelizable_areas"].append({"area": "api", "paths": [f"{d}/"]})

    for area, paths in (
        ("ui", ["ui", "src/components", "apps/web", "frontend", "DevLinker-Frontend"]),
        ("api", ["api", "src/server", "apps/api", "backend", "DevLinker-backend"]),
        ("tests", ["tests", "test", "__tests__", "spec"]),
        ("docs", ["docs", "doc", "README.md"]),
        ("infra", ["infra", "deploy", ".github"]),
    ):
        found = [p for p in paths if (repo_root / p.split("/")[0]).exists() or p in dirs]
        if found:
            analysis["parallelizable_areas"].append({"area": area, "paths": found})
            analysis["ownership_hints"][area] = found

    if (repo_root / "a3-polyglot" / "main.py").exists():
        analysis["parallelizable_areas"].append(
            {
                "area": "polyglot_extensions",
                "paths": ["a3-polyglot/routers/", "a3-polyglot/tests/"],
                "note": "CSV export, thresholds, audit log lanes",
            }
        )

    analysis["recommended_verification"] = _default_verify_commands(repo_root, analysis)
    return analysis


def _default_verify_commands(repo_root: Path, analysis: dict[str, Any]) -> list[str]:
    cmds: list[str] = []
    pkg = repo_root / "package.json"
    if pkg.exists():
        try:
            scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
            for key in ("lint", "build", "test"):
                if key in scripts:
                    cmds.append(f"npm run {key}")
        except json.JSONDecodeError:
            pass
    if (repo_root / "a3-polyglot").exists():
        cmds.append("bash shared/lib/verify.sh a3-polyglot")
    elif "python" in analysis.get("languages", []):
        cmds.append("python3 -m pytest -q")
    if not cmds:
        cmds.append("echo 'no verify commands detected — set verification_commands in discovery'")
    return cmds
