"""Merge workspace phase artifacts into dashboard_data.json (UI single source of truth)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.json_writer import JsonWriter

SCHEMA_VERSION = "1.0"


@dataclass
class SourceRecord:
    """Metadata for one upstream JSON artifact."""

    key: str
    relative_path: str
    absolute_path: str
    present: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "relative_path": self.relative_path,
            "absolute_path": self.absolute_path,
            "present": self.present,
            "error": self.error,
        }


@dataclass
class DashboardBuildResult:
    repo_name: str
    repo_path: str
    workspace_dir: str
    output_path: str
    payload: Dict[str, Any] = field(default_factory=dict)
    sources: List[SourceRecord] = field(default_factory=list)

    @property
    def complete_sources(self) -> int:
        return sum(1 for s in self.sources if s.present)

    @property
    def missing_sources(self) -> List[str]:
        return [s.key for s in self.sources if not s.present]


class DashboardDataBuilder:
    """Read B1/B2/B3/graph/generated status JSON and write dashboard_data.json."""

    INVENTORY_REL = os.path.join("B1_inventory", "inventory.json")
    ROUTES_REL = os.path.join("B2_routes", "routes.json")
    TESTS_REL = os.path.join("B3_tests", "tests.json")
    GRAPHS_REL = os.path.join("graphs", "graph_data.json")
    OUTPUT_NAME = "dashboard_data.json"

    def __init__(self, workspace_root: str = "workspace") -> None:
        self.workspace_root = workspace_root
        self.json_writer = JsonWriter()

    def build(
        self,
        repo_path: str,
        *,
        workspace_dir: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> DashboardBuildResult:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"not a directory: {repo_path}")

        repo_name = self.repo_name(repo_path)
        ws_dir = workspace_dir or os.path.join(
            self.workspace_root, repo_name
        )
        ws_dir = os.path.abspath(ws_dir)
        out_path = output_path or os.path.join(ws_dir, self.OUTPUT_NAME)

        inventory_src = os.path.join(ws_dir, self.INVENTORY_REL)
        routes_src = os.path.join(ws_dir, self.ROUTES_REL)
        tests_src = os.path.join(ws_dir, self.TESTS_REL)
        graphs_src = os.path.join(ws_dir, self.GRAPHS_REL)

        inventory, inv_src = self._load_source("inventory", inventory_src, ws_dir)
        routes, routes_src_rec = self._load_source("routes", routes_src, ws_dir)
        tests, tests_src_rec = self._load_source("tests", tests_src, ws_dir)
        graphs, graphs_src_rec = self._load_source("graphs", graphs_src, ws_dir)
        generated, gen_sources = self._load_generated_projects(ws_dir)

        sources = [
            inv_src,
            routes_src_rec,
            tests_src_rec,
            graphs_src_rec,
            *gen_sources,
        ]

        payload = self._compose_payload(
            repo_path=repo_path,
            repo_name=repo_name,
            workspace_dir=ws_dir,
            inventory=inventory,
            routes=routes,
            tests=tests,
            graphs=graphs,
            generated_projects=generated,
            sources=sources,
        )

        self.json_writer.write(out_path, payload)

        return DashboardBuildResult(
            repo_name=repo_name,
            repo_path=repo_path,
            workspace_dir=ws_dir,
            output_path=os.path.abspath(out_path),
            payload=payload,
            sources=sources,
        )

    @staticmethod
    def repo_name(repo_path: str) -> str:
        return os.path.basename(repo_path.rstrip(os.sep)) or "repository"

    def _load_source(
        self, key: str, path: str, workspace_dir: str
    ) -> tuple[Optional[Any], SourceRecord]:
        path = os.path.abspath(path)
        rel = os.path.relpath(path, workspace_dir) if path.startswith(workspace_dir) else path
        if not os.path.isfile(path):
            return None, SourceRecord(
                key=key,
                relative_path=rel,
                absolute_path=path,
                present=False,
                error="file not found",
            )
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            return None, SourceRecord(
                key=key,
                relative_path=rel,
                absolute_path=path,
                present=False,
                error=str(exc),
            )
        return data, SourceRecord(
            key=key,
            relative_path=rel,
            absolute_path=path,
            present=True,
        )

    def _load_generated_projects(
        self, workspace_dir: str
    ) -> tuple[Dict[str, Any], List[SourceRecord]]:
        base = os.path.join(workspace_dir, "generated_projects")
        projects: Dict[str, Any] = {}
        sources: List[SourceRecord] = []

        if not os.path.isdir(base):
            sources.append(
                SourceRecord(
                    key="generated_projects",
                    relative_path="generated_projects",
                    absolute_path=base,
                    present=False,
                    error="directory not found",
                )
            )
            return projects, sources

        found_any = False
        for name in sorted(os.listdir(base)):
            proj_dir = os.path.join(base, name)
            if not os.path.isdir(proj_dir):
                continue
            status_path = os.path.join(proj_dir, "status.json")
            data, rec = self._load_source(f"status:{name}", status_path, workspace_dir)
            sources.append(rec)
            if data is not None:
                projects[name] = data
                found_any = True

        if not found_any and not sources:
            sources.append(
                SourceRecord(
                    key="generated_projects",
                    relative_path="generated_projects",
                    absolute_path=base,
                    present=False,
                    error="no status.json files found",
                )
            )

        return projects, sources

    def _compose_payload(
        self,
        *,
        repo_path: str,
        repo_name: str,
        workspace_dir: str,
        inventory: Optional[Any],
        routes: Optional[Any],
        tests: Optional[Any],
        graphs: Optional[Any],
        generated_projects: Dict[str, Any],
        sources: List[SourceRecord],
    ) -> dict:
        repo_from_sources = (
            (inventory or {}).get("repo")
            or (routes or {}).get("repo")
            or (tests or {}).get("repo")
            or (graphs or {}).get("repo")
            or repo_path
        )
        name_from_sources = (
            (inventory or {}).get("repo_name")
            or (routes or {}).get("repo_name")
            or (tests or {}).get("repo_name")
            or (graphs or {}).get("repo_name")
            or repo_name
        )

        return {
            "schema_version": SCHEMA_VERSION,
            "role": "dashboard_ssot",
            "repo": repo_from_sources,
            "repo_name": name_from_sources,
            "repo_path": repo_path,
            "workspace_dir": workspace_dir,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": [s.to_dict() for s in sources],
            "inventory": inventory,
            "routes": routes,
            "tests": tests,
            "graphs": graphs,
            "generated_projects": generated_projects,
            "summary": self._build_summary(
                inventory, routes, tests, graphs, generated_projects, sources
            ),
        }

    @staticmethod
    def _build_summary(
        inventory: Optional[Any],
        routes: Optional[Any],
        tests: Optional[Any],
        graphs: Optional[Any],
        generated_projects: Dict[str, Any],
        sources: List[SourceRecord],
    ) -> dict:
        inv_counts = (inventory or {}).get("counts") or {}
        route_counts = (routes or {}).get("counts") or {}
        graph_types = list(((graphs or {}).get("graphs") or {}).keys())

        greenfield = {
            name: proj.get("status", "UNKNOWN")
            for name, proj in generated_projects.items()
        }

        tests_exec = (tests or {}).get("execution") or {}
        tests_status = (tests or {}).get("status") or tests_exec.get("status")

        core_keys = {"inventory", "routes", "tests", "graphs"}
        core_present = {
            s.key: s.present for s in sources if s.key in core_keys
        }

        return {
            "sources_loaded": sum(1 for s in sources if s.present),
            "sources_total": len(sources),
            "core": core_present,
            "pipelines": {
                "B1_inventory": "complete" if inventory else "missing",
                "B2_routes": "complete" if routes else "missing",
                "B3_tests": "complete" if tests else "missing",
                "graphs": "complete" if graphs else "missing",
                "greenfield": greenfield or None,
            },
            "counts": {
                "artifacts_total": sum(inv_counts.values()) if inv_counts else None,
                "artifact_breakdown": inv_counts or None,
                "routes_total": route_counts.get("total"),
                "routes_backend": route_counts.get("backend"),
                "routes_frontend": route_counts.get("frontend"),
                "tests_passed": (tests or {}).get("passed"),
                "tests_failed": (tests or {}).get("failed"),
                "tests_status": tests_status,
                "graph_types": graph_types or None,
                "greenfield_projects": len(generated_projects),
            },
        }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Merge workspace JSON artifacts into dashboard_data.json"
    )
    ap.add_argument("repo", help="repository path (used for repo_name / workspace dir)")
    ap.add_argument("--workspace", default="workspace", help="workspace root directory")
    ap.add_argument(
        "--workspace-dir",
        help="override workspace/{repo_name} directory (source + default output parent)",
    )
    ap.add_argument("--output", help="override dashboard_data.json output path")
    args = ap.parse_args(argv)

    try:
        result = DashboardDataBuilder(workspace_root=args.workspace).build(
            args.repo,
            workspace_dir=args.workspace_dir,
            output_path=args.output,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    summary = result.payload.get("summary", {})
    print(f"Dashboard SSOT written: {result.output_path}")
    print(f"  repo        : {result.repo_name}")
    print(f"  sources     : {result.complete_sources}/{len(result.sources)} loaded")
    if result.missing_sources:
        print(f"  missing     : {', '.join(result.missing_sources)}")
    pipelines = summary.get("pipelines", {})
    print(f"  pipelines   : B1={pipelines.get('B1_inventory')} B2={pipelines.get('B2_routes')} "
          f"B3={pipelines.get('B3_tests')} graphs={pipelines.get('graphs')}")
    gf = pipelines.get("greenfield")
    if gf:
        print(f"  greenfield  : {gf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
