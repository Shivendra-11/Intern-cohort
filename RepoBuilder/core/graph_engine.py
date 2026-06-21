"""NetworkX-backed graph models for repository intelligence."""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import networkx as nx

from core.file_scanner import FileScanner
from core.inventory_agent import InventoryAgent, InventoryItem
from core.json_writer import JsonWriter
from core.route_agent import RouteAgent, RouteRecord
from core.test_discovery import TestDiscovery

# --- import extraction patterns ---------------------------------------------
PY_IMPORT = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE
)
JS_IMPORT = re.compile(
    r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))"""
)
JAVA_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)", re.MULTILINE)
GO_IMPORT = re.compile(r'import\s+(?:"([^"]+)"|(\([\s\S]*?\)))')
RUST_USE = re.compile(r"^\s*use\s+([\w:]+)", re.MULTILINE)

PY_CLASS_BASES = re.compile(r"^\s*class\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE)
JS_CLASS_EXTENDS = re.compile(r"class\s+(\w+)\s+extends\s+(\w+)")
JAVA_CLASS_EXTENDS = re.compile(r"class\s+(\w+)\s+extends\s+(\w+)")

SERVICE_TYPES = {"services", "controllers", "repositories", "models"}


@dataclass
class GraphModel:
    """Serializable graph: nodes, edges, metadata."""

    graph_type: str
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "graph_type": self.graph_type,
            "nodes": self.nodes,
            "edges": self.edges,
            "metadata": self.metadata,
        }


class GraphEngine:
    """Build repository graphs using NetworkX and export JSON models."""

    GRAPH_TYPES = (
        "import",
        "class_dependencies",
        "service",
        "route",
        "test",
    )

    def __init__(self, scanner: FileScanner | None = None) -> None:
        self.scanner = scanner or FileScanner()
        self.json_writer = JsonWriter()

    def build_all(self, repo_path: str) -> dict[str, GraphModel]:
        repo_path = os.path.abspath(repo_path)
        inventory = InventoryAgent(scanner=self.scanner).build_inventory(
            repo_path, InventoryAgent.repo_name(repo_path)
        )
        routes = RouteAgent(scanner=self.scanner).discover(
            repo_path, InventoryAgent.repo_name(repo_path)
        )
        test_setups = TestDiscovery(scanner=self.scanner).discover(repo_path)

        return {
            "import": self.build_import_graph(repo_path),
            "class_dependencies": self.build_class_dependency_graph(repo_path),
            "service": self.build_service_graph(inventory.items),
            "route": self.build_route_graph(routes.all_routes),
            "test": self.build_test_graph(
                test_setups[0].test_files if test_setups else [],
                test_setups[0].framework if test_setups else None,
                repo_path,
            ),
        }

    def build_import_graph(self, repo_path: str) -> GraphModel:
        G = nx.DiGraph()
        module_ids: dict[str, str] = {}

        for abs_path, lang in self.scanner.iter_source_files(repo_path):
            rel = os.path.relpath(abs_path, repo_path)
            file_id = f"file:{rel}"
            G.add_node(file_id, kind="file", label=rel, file=rel)

            for imp in self._extract_imports(abs_path, lang):
                mod_id = f"module:{imp}"
                if mod_id not in module_ids:
                    module_ids[imp] = mod_id
                    G.add_node(mod_id, kind="module", label=imp)
                G.add_edge(file_id, mod_id, relation="imports")

        return self._export(G, "import", {"description": "File → imported module"})

    def build_class_dependency_graph(self, repo_path: str) -> GraphModel:
        G = nx.DiGraph()
        known_classes: dict[str, str] = {}

        for abs_path, lang in self.scanner.iter_source_files(repo_path):
            rel = os.path.relpath(abs_path, repo_path)
            text = "\n".join(self.scanner.read_lines(abs_path))
            for cls, _bases in self._extract_class_deps(text, lang):
                cls_id = f"class:{rel}:{cls}"
                G.add_node(cls_id, kind="class", name=cls, file=rel)
                known_classes[cls] = cls_id

        for abs_path, lang in self.scanner.iter_source_files(repo_path):
            rel = os.path.relpath(abs_path, repo_path)
            text = "\n".join(self.scanner.read_lines(abs_path))
            for cls, bases in self._extract_class_deps(text, lang):
                cls_id = f"class:{rel}:{cls}"
                for base in bases:
                    target = known_classes.get(base)
                    if target and target != cls_id:
                        G.add_edge(cls_id, target, relation="extends")
                    elif base:
                        ext_id = f"class:external:{base}"
                        G.add_node(ext_id, kind="class", name=base, file="(external)")
                        G.add_edge(cls_id, ext_id, relation="extends")

        return self._export(
            G, "class_dependencies", {"description": "Class inheritance / dependency"}
        )

    def build_service_graph(self, items: list[InventoryItem]) -> GraphModel:
        G = nx.Graph()
        service_items = [i for i in items if i.type in SERVICE_TYPES]

        for item in service_items:
            nid = item.node_id()
            G.add_node(
                nid,
                kind=item.type,
                name=item.name,
                file=item.file,
                line=item.line,
            )

        names = {i.name: i for i in service_items}
        for item in service_items:
            src = item.node_id()
            # Naming convention edges: FooService → FooController, FooRepository.
            stem = re.sub(r"(Service|Controller|Repository|Model)$", "", item.name)
            if not stem or len(stem) < 2:
                continue
            for suffix, rel_type in (
                ("Service", "paired_service"),
                ("Controller", "paired_controller"),
                ("Repository", "paired_repository"),
                ("Model", "paired_model"),
            ):
                peer_name = stem + suffix
                peer = names.get(peer_name)
                if peer and peer.node_id() != src:
                    G.add_edge(src, peer.node_id(), relation=rel_type)

        # Co-location edges within same file.
        by_file: dict[str, list[InventoryItem]] = {}
        for item in service_items:
            by_file.setdefault(item.file, []).append(item)
        for file_path, group in by_file.items():
            for i, a in enumerate(group):
                for b in group[i + 1 :]:
                    G.add_edge(a.node_id(), b.node_id(), relation="same_file", file=file_path)

        return self._export(G, "service", {"description": "Service / controller / model layer"})

    def build_route_graph(self, routes: list[RouteRecord]) -> GraphModel:
        G = nx.DiGraph()
        for r in routes:
            G.add_node(
                r.node_id(),
                kind="route",
                method=r.method,
                path=r.path,
                file=r.file,
                framework=r.framework,
                surface=r.surface,
            )

        by_file: dict[str, list[RouteRecord]] = {}
        for r in routes:
            by_file.setdefault(r.file, []).append(r)
        for file_path, group in by_file.items():
            ids = [x.node_id() for x in group]
            for i, a in enumerate(ids):
                for b in ids[i + 1 :]:
                    G.add_edge(a, b, relation="same_file", file=file_path)

        sorted_routes = sorted(routes, key=lambda x: (len(x.path), x.path))
        for i, parent in enumerate(sorted_routes):
            for child in sorted_routes[i + 1 :]:
                if child.path != parent.path and child.path.startswith(
                    parent.path.rstrip("/") + "/"
                ):
                    G.add_edge(
                        parent.node_id(), child.node_id(), relation="path_prefix"
                    )

        return self._export(G, "route", {"description": "HTTP and frontend routes"})

    def build_test_graph(
        self,
        test_files: list[str],
        framework: str | None,
        repo_path: str,
    ) -> GraphModel:
        G = nx.DiGraph()
        source_files = {
            os.path.relpath(p, repo_path)
            for p, _ in self.scanner.iter_source_files(repo_path)
        }

        for tf in test_files:
            if tf.startswith("("):
                continue
            tid = f"test:{tf}"
            G.add_node(tid, kind="test", file=tf, framework=framework or "unknown")
            candidates = self._guess_test_targets(tf, source_files)
            for src in candidates:
                sid = f"file:{src}"
                G.add_node(sid, kind="source", file=src)
                G.add_edge(tid, sid, relation="tests")

        return self._export(
            G,
            "test",
            {
                "description": "Test file → likely source under test",
                "framework": framework,
            },
        )

    def compose_graph_data(
        self, repo_path: str, graphs: dict[str, GraphModel]
    ) -> dict:
        repo_path = os.path.abspath(repo_path)
        repo_name = os.path.basename(repo_path.rstrip(os.sep)) or "repository"
        return {
            "repo": repo_path,
            "repo_name": repo_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "engine": "networkx",
            "graphs": {name: model.to_dict() for name, model in graphs.items()},
            "metadata": {
                "graph_types": list(graphs.keys()),
                "total_nodes": sum(m.metadata.get("node_count", 0) for m in graphs.values()),
                "total_edges": sum(m.metadata.get("edge_count", 0) for m in graphs.values()),
            },
        }

    def write_graph_data(
        self,
        repo_path: str,
        output_path: str | None = None,
        workspace_root: str = "workspace",
    ) -> str:
        repo_path = os.path.abspath(repo_path)
        repo_name = os.path.basename(repo_path.rstrip(os.sep)) or "repository"
        graphs = self.build_all(repo_path)
        payload = self.compose_graph_data(repo_path, graphs)

        if output_path is None:
            output_path = os.path.join(workspace_root, repo_name, "graphs", "graph_data.json")
        self.json_writer.write(output_path, payload)
        return output_path

    # --- helpers ----------------------------------------------------------------

    def _export(self, G: nx.Graph, graph_type: str, metadata: dict) -> GraphModel:
        nodes = [{"id": nid, **attrs} for nid, attrs in G.nodes(data=True)]
        edges = [
            {"source": u, "target": v, **attrs} for u, v, attrs in G.edges(data=True)
        ]
        meta = {
            **metadata,
            "graph_type": graph_type,
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "directed": isinstance(G, nx.DiGraph),
        }
        return GraphModel(graph_type=graph_type, nodes=nodes, edges=edges, metadata=meta)

    def _extract_imports(self, path: str, lang: str) -> set[str]:
        text = "\n".join(self.scanner.read_lines(path))
        imports: set[str] = set()
        if lang == "python":
            for m in PY_IMPORT.finditer(text):
                imports.add(m.group(1) or m.group(2))
        elif lang in ("javascript", "typescript"):
            for m in JS_IMPORT.finditer(text):
                imports.add(m.group(1) or m.group(2))
        elif lang in ("java", "kotlin"):
            for m in JAVA_IMPORT.finditer(text):
                imports.add(m.group(1))
        elif lang == "go":
            for m in GO_IMPORT.finditer(text):
                if m.group(1):
                    imports.add(m.group(1))
        elif lang == "rust":
            for m in RUST_USE.finditer(text):
                imports.add(m.group(1))
        return {i for i in imports if i}

    def _extract_class_deps(self, text: str, lang: str) -> list[tuple[str, list[str]]]:
        out: list[tuple[str, list[str]]] = []
        if lang == "python":
            for m in PY_CLASS_BASES.finditer(text):
                bases = [
                    b.strip().split(".")[-1]
                    for b in m.group(2).split(",")
                    if b.strip() and b.strip() not in ("object",)
                ]
                out.append((m.group(1), bases))
        elif lang in ("javascript", "typescript"):
            for m in JS_CLASS_EXTENDS.finditer(text):
                out.append((m.group(1), [m.group(2)]))
        elif lang in ("java", "kotlin"):
            for m in JAVA_CLASS_EXTENDS.finditer(text):
                out.append((m.group(1), [m.group(2)]))
        return out

    @staticmethod
    def _guess_test_targets(test_file: str, source_files: set[str]) -> list[str]:
        """Heuristic: map test_foo.py → foo.py, foo.test.js → foo.js."""
        base = os.path.basename(test_file)
        candidates: list[str] = []
        patterns: list[str] = []

        if base.startswith("test_") and base.endswith(".py"):
            patterns.append(base[5:])
        if base.endswith("_test.py"):
            patterns.append(base[:-8] + ".py")
        m = re.match(r"(.+)\.(test|spec)\.(jsx?|tsx?)$", base)
        if m:
            patterns.append(m.group(1) + "." + m.group(3))

        for pat in patterns:
            for src in source_files:
                if os.path.basename(src) == pat:
                    candidates.append(src)
                if src.endswith(pat):
                    candidates.append(src)

        # Same directory stem match: tests/test_x.py → ../module_x.py
        stem = re.sub(r"^(test_|.*\.(test|spec)\.)", "", base).split(".")[0]
        if stem:
            for src in source_files:
                if stem in os.path.basename(src):
                    candidates.append(src)

        return sorted(set(candidates))[:5]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build repository graphs (NetworkX)")
    ap.add_argument("repo", help="path to repository")
    ap.add_argument("--workspace", default="workspace")
    ap.add_argument("--output", help="output path for graph_data.json")
    args = ap.parse_args(argv)

    try:
        path = GraphEngine().write_graph_data(
            args.repo,
            output_path=args.output,
            workspace_root=args.workspace,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Graph data written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
