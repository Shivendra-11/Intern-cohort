"""B2 route agent — discover backend and frontend routes, write workspace outputs."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.file_scanner import FileScanner
from core.json_writer import JsonWriter
from core.report_generator import ReportGenerator, ReportSection
from core.route_ast import AstRoute
from core.route_dedupe import dedupe_backend_routes, dedupe_frontend_routes
from core.route_scanners import scan_repo

NOISE_PATH_PARTS = ("/test/", "/tests/", "/__tests__/", "/docs/", "/examples/")


@dataclass(frozen=True)
class RouteRecord:
    method: str
    path: str
    file: str
    line: int = 0
    framework: str = ""
    surface: str = "backend"
    handler: str = ""

    def node_id(self) -> str:
        return f"{self.surface}:{self.method}:{self.path}:{self.file}:{self.line}"


@dataclass
class RouteDiscoveryResult:
    repo: str
    repo_name: str
    backend: List[RouteRecord] = field(default_factory=list)
    frontend: List[RouteRecord] = field(default_factory=list)
    production_backend: List[RouteRecord] = field(default_factory=list)
    production_frontend: List[RouteRecord] = field(default_factory=list)

    @property
    def all_routes(self) -> List[RouteRecord]:
        return self.backend + self.frontend

    def to_routes_json(self) -> dict:
        return {
            "repo": self.repo,
            "repo_name": self.repo_name,
            "counts": {
                "backend": len(self.backend),
                "frontend": len(self.frontend),
                "production_backend": len(self.production_backend),
                "production_frontend": len(self.production_frontend),
                "total": len(self.all_routes),
            },
            "backend": [self._route_dict(r) for r in self.backend],
            "frontend": [self._route_dict(r) for r in self.frontend],
            "routes": [self._route_dict(r) for r in self.all_routes],
        }

    @staticmethod
    def _route_dict(r: RouteRecord) -> dict:
        return {
            "method": r.method,
            "path": r.path,
            "file": r.file,
            "line": r.line,
            "framework": r.framework,
            "surface": r.surface,
            "handler": r.handler,
        }


class RouteAgent:
    """Discover routes and write workspace/{repo_name}/B2_routes/ artifacts."""

    def __init__(
        self,
        scanner: Optional[FileScanner] = None,
        workspace_root: str = "workspace",
    ) -> None:
        self.scanner = scanner or FileScanner()
        self.workspace_root = workspace_root
        self.json_writer = JsonWriter()
        self.report_gen = ReportGenerator()

    def run(self, repo_path: str, output_dir: Optional[str] = None) -> RouteDiscoveryResult:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"not a directory: {repo_path}")

        repo_name = self.repo_name(repo_path)
        out_dir = output_dir or os.path.join(
            self.workspace_root, repo_name, "B2_routes"
        )

        result = self.discover(repo_path, repo_name)
        graph = self.build_route_graph(result.all_routes)

        os.makedirs(out_dir, exist_ok=True)
        self.json_writer.write(os.path.join(out_dir, "routes.json"), result.to_routes_json())
        self.json_writer.write(os.path.join(out_dir, "route_graph.json"), graph)
        with open(os.path.join(out_dir, "routes.md"), "w", encoding="utf-8") as fh:
            fh.write(self.render_markdown(result))

        return result

    @staticmethod
    def repo_name(repo_path: str) -> str:
        return os.path.basename(repo_path.rstrip(os.sep)) or "repository"

    def discover(self, repo_path: str, repo_name: str) -> RouteDiscoveryResult:
        backend_raw, frontend_raw = scan_repo(repo_path)
        backend = dedupe_backend_routes([self._convert(r, "backend") for r in backend_raw])
        frontend = dedupe_frontend_routes([self._convert(r, "frontend") for r in frontend_raw])

        return RouteDiscoveryResult(
            repo=repo_path,
            repo_name=repo_name,
            backend=backend,
            frontend=frontend,
            production_backend=[r for r in backend if not self._is_noise(r.file)],
            production_frontend=[r for r in frontend if not self._is_noise(r.file)],
        )

    @staticmethod
    def _convert(r: AstRoute, surface: str) -> RouteRecord:
        return RouteRecord(
            method=r.method,
            path=r.path,
            file=r.file,
            line=r.line,
            framework=r.framework,
            surface=surface,
            handler=r.handler,
        )

    @staticmethod
    def _is_noise(file_path: str) -> bool:
        low = "/" + file_path.lower().replace("\\", "/")
        return any(part in low for part in NOISE_PATH_PARTS)

    @staticmethod
    def build_route_graph(routes: List[RouteRecord]) -> dict:
        nodes = [
            {
                "id": r.node_id(),
                "method": r.method,
                "path": r.path,
                "file": r.file,
                "line": r.line,
                "framework": r.framework,
                "surface": r.surface,
            }
            for r in routes
        ]
        edges: List[dict] = []

        # Same file adjacency.
        by_file: Dict[str, List[RouteRecord]] = {}
        for r in routes:
            by_file.setdefault(r.file, []).append(r)
        for file_path, group in by_file.items():
            ids = [x.node_id() for x in group]
            for i, a in enumerate(ids):
                for b in ids[i + 1 :]:
                    edges.append(
                        {"source": a, "target": b, "relation": "same_file", "file": file_path}
                    )

        # Path prefix hierarchy (parent → child).
        sorted_routes = sorted(routes, key=lambda x: (len(x.path), x.path))
        for i, parent in enumerate(sorted_routes):
            for child in sorted_routes[i + 1 :]:
                if child.path != parent.path and child.path.startswith(
                    parent.path.rstrip("/") + "/"
                ):
                    edges.append(
                        {
                            "source": parent.node_id(),
                            "target": child.node_id(),
                            "relation": "path_prefix",
                        }
                    )

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def render_markdown(self, result: RouteDiscoveryResult) -> str:
        sections: List[ReportSection] = [
            ReportSection(
                title="Summary",
                body=self.report_gen.key_values(
                    [
                        ("Repository", result.repo),
                        ("Backend routes", len(result.backend)),
                        ("Frontend routes", len(result.frontend)),
                        ("Production backend", len(result.production_backend)),
                        ("Production frontend", len(result.production_frontend)),
                    ]
                ),
            )
        ]

        if result.production_backend:
            rows = [
                [r.method, r.path, r.file, r.framework]
                for r in result.production_backend
            ]
            sections.append(
                ReportSection(
                    title="Backend Routes",
                    body=self.report_gen.table(
                        ["Method", "Path", "File", "Framework"], rows
                    ),
                )
            )

        if result.production_frontend:
            rows = [
                [r.method, r.path, r.file, r.framework]
                for r in result.production_frontend
            ]
            sections.append(
                ReportSection(
                    title="Frontend Routes",
                    body=self.report_gen.table(
                        ["Method", "Path", "File", "Framework"], rows
                    ),
                )
            )

        return self.report_gen.generate(
            f"Routes — {result.repo_name}",
            sections,
            footer=self.report_gen.timestamp_footer("route_agent"),
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="B2 route discovery agent")
    ap.add_argument("repo", help="path to repository")
    ap.add_argument("--workspace", default="workspace", help="workspace root")
    ap.add_argument("--output-dir", help="override B2_routes output directory")
    args = ap.parse_args(argv)

    try:
        result = RouteAgent(workspace_root=args.workspace).run(
            args.repo, output_dir=args.output_dir
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = args.output_dir or os.path.join(
        args.workspace, result.repo_name, "B2_routes"
    )
    print("Route discovery complete")
    print(f"  output   : {os.path.abspath(out)}")
    print(f"  backend  : {len(result.backend)}")
    print(f"  frontend : {len(result.frontend)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
