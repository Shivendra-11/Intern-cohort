"""B1 inventory agent — discover and classify repository artifacts.

Prefers tree-sitter AST parsing; falls back to regex heuristics when grammars
are unavailable. Writes workspace/{repo_name}/B1_inventory/ outputs.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field

from core.file_scanner import FileScanner
from core.inventory_ast import RawDefinition, available_parsers, parse_definitions
from core.json_writer import JsonWriter
from core.report_generator import ReportGenerator, ReportSection

# Categories requested for B1 (no "components" — utilities covers helpers).
CATEGORIES = [
    "classes",
    "interfaces",
    "services",
    "controllers",
    "models",
    "repositories",
    "jobs",
    "consumers",
    "configs",
    "utilities",
]

DECORATOR_CAT = [
    (re.compile(r"@(RestController|Controller)\b"), "controllers"),
    (re.compile(r"@Service\b"), "services"),
    (re.compile(r"@Injectable\b"), "services"),
    (re.compile(r"@Repository\b"), "repositories"),
    (re.compile(r"@Entity\b"), "models"),
    (re.compile(r"@(Document|Schema)\b"), "models"),
    (re.compile(r"@(Scheduled|Cron)\b"), "jobs"),
    (re.compile(r"@(shared_task|periodic_task|celery\.task|app\.task)\b"), "jobs"),
    (re.compile(r"@(KafkaListener|RabbitListener|EventPattern|MessagePattern|SqsListener)\b"), "consumers"),
]

BASE_HINTS = [
    (re.compile(r"\b(BaseModel|models\.Model|declarative_base|Base)\b"), "models"),
    (re.compile(r"\(\s*Protocol\s*\)|\(\s*ABC\s*\)|\(\s*ABCMeta\b"), "interfaces"),
]

PATH_CAT = [
    (re.compile(r"(^|/)(controllers?)(/|$)|controller\.\w+$"), "controllers"),
    (re.compile(r"(^|/)(services?)(/|$)|service\.\w+$"), "services"),
    (re.compile(r"(^|/)(repositor(y|ies))(/|$)|repository\.\w+$"), "repositories"),
    (re.compile(r"(^|/)(models?|entities|schemas?)(/|$)|model\.\w+$"), "models"),
    (re.compile(r"(^|/)(jobs?|tasks?|workers?)(/|$)|(job|worker)\.\w+$"), "jobs"),
    (re.compile(r"(^|/)(consumers?|listeners?|subscribers?)(/|$)|consumer\.\w+$"), "consumers"),
    (re.compile(r"(^|/)(utils?|helpers?|common|lib)(/|$)|(util|helper)s?\.\w+$"), "utilities"),
]

# Regex fallback patterns (used only when tree-sitter unavailable for a file).
REGEX_PATTERNS = {
    "python": [
        (re.compile(r"^\s*class\s+(\w+)\s*(\([^)]*\))?"), "class"),
        (re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\("), "function"),
    ],
    "javascript": [
        (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("), "function"),
    ],
    "typescript": [
        (re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:export\s+)?interface\s+(\w+)"), "interface"),
        (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("), "function"),
    ],
    "java": [
        (re.compile(r"\b(?:public|private|protected)?\s*(?:abstract\s+|final\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"\binterface\s+(\w+)"), "interface"),
    ],
    "go": [
        (re.compile(r"^\s*type\s+(\w+)\s+struct\b"), "class"),
        (re.compile(r"^\s*type\s+(\w+)\s+interface\b"), "interface"),
    ],
    "rust": [
        (re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:pub\s+)?trait\s+(\w+)"), "interface"),
        (re.compile(r"^\s*(?:pub\s+)?enum\s+(\w+)"), "class"),
    ],
}


@dataclass(frozen=True)
class InventoryItem:
    name: str
    type: str  # category: services, controllers, ...
    file: str
    line: int
    syntactic_kind: str = ""
    signature: str = ""

    def node_id(self) -> str:
        return f"{self.type}:{self.file}:{self.line}:{self.name}"


@dataclass
class InventoryResult:
    repo: str
    repo_name: str
    parser_mode: str
    parsers_available: list[str]
    counts: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, list[InventoryItem]] = field(default_factory=dict)
    items: list[InventoryItem] = field(default_factory=list)

    def to_inventory_json(self) -> dict:
        return {
            "repo": self.repo,
            "repo_name": self.repo_name,
            "parser_mode": self.parser_mode,
            "parsers_available": self.parsers_available,
            "counts": self.counts,
            "artifacts": {
                cat: [self._item_dict(i) for i in self.by_category.get(cat, [])]
                for cat in CATEGORIES
            },
            "items": [self._item_dict(i) for i in self.items],
        }

    @staticmethod
    def _item_dict(item: InventoryItem) -> dict:
        return {
            "name": item.name,
            "type": item.type,
            "file": item.file,
            "line": item.line,
            "syntactic_kind": item.syntactic_kind,
            "signature": item.signature,
        }


class InventoryAgent:
    """Discover repository artifacts and write B1 workspace outputs."""

    def __init__(
        self,
        scanner: FileScanner | None = None,
        workspace_root: str = "workspace",
    ) -> None:
        self.scanner = scanner or FileScanner()
        self.workspace_root = workspace_root
        self.json_writer = JsonWriter()
        self.report_gen = ReportGenerator()

    def run(self, repo_path: str, output_dir: str | None = None) -> InventoryResult:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"not a directory: {repo_path}")

        repo_name = self.repo_name(repo_path)
        out_dir = output_dir or os.path.join(
            self.workspace_root, repo_name, "B1_inventory"
        )

        result = self.build_inventory(repo_path, repo_name)
        graph = self.build_graph(result.items)

        os.makedirs(out_dir, exist_ok=True)
        self.json_writer.write(
            os.path.join(out_dir, "inventory.json"),
            result.to_inventory_json(),
        )
        self.json_writer.write(os.path.join(out_dir, "graph_data.json"), graph)
        with open(os.path.join(out_dir, "inventory.md"), "w", encoding="utf-8") as fh:
            fh.write(self.render_markdown(result))

        return result

    @staticmethod
    def repo_name(repo_path: str) -> str:
        name = os.path.basename(repo_path.rstrip(os.sep))
        return name or "repository"

    def build_inventory(self, repo_path: str, repo_name: str) -> InventoryResult:
        parsers = available_parsers()
        ast_files = 0
        regex_files = 0

        buckets: dict[str, list[InventoryItem]] = {c: [] for c in CATEGORIES}

        for abs_path, lang in self.scanner.iter_source_files(repo_path):
            rel = os.path.relpath(abs_path, repo_path)
            defs = parse_definitions(abs_path, lang)
            if defs is not None:
                ast_files += 1
                for d in defs:
                    cat = self.classify(d, rel)
                    if cat:
                        buckets[cat].append(self._to_item(d, cat, rel))
            else:
                regex_files += 1
                for d in self._regex_definitions(abs_path, lang):
                    cat = self.classify(d, rel)
                    if cat:
                        buckets[cat].append(self._to_item(d, cat, rel))

        self._add_configs(repo_path, buckets)

        # De-duplicate and sort.
        for cat in CATEGORIES:
            seen: set[tuple[str, str, int]] = set()
            unique: list[InventoryItem] = []
            for item in buckets[cat]:
                key = (item.name, item.file, item.line)
                if key in seen:
                    continue
                seen.add(key)
                unique.append(item)
            buckets[cat] = sorted(unique, key=lambda x: (x.file, x.line, x.name))

        flat: list[InventoryItem] = []
        for cat in CATEGORIES:
            flat.extend(buckets[cat])

        mode = "tree-sitter" if ast_files and regex_files == 0 else (
            "hybrid" if ast_files and regex_files else "regex"
        )

        counts = {c: len(buckets[c]) for c in CATEGORIES}
        return InventoryResult(
            repo=repo_path,
            repo_name=repo_name,
            parser_mode=mode,
            parsers_available=parsers,
            counts=counts,
            by_category=buckets,
            items=flat,
        )

    def _add_configs(self, repo_path: str, buckets: dict[str, list[InventoryItem]]) -> None:
        for abs_path in self.scanner.iter_files(repo_path):
            if not self.scanner.is_config_file(abs_path):
                continue
            rel = os.path.relpath(abs_path, repo_path)
            buckets["configs"].append(
                InventoryItem(
                    name=os.path.basename(abs_path),
                    type="configs",
                    file=rel,
                    line=1,
                    syntactic_kind="config",
                    signature="(config file)",
                )
            )

    @staticmethod
    def _to_item(d: RawDefinition, category: str, rel_path: str) -> InventoryItem:
        return InventoryItem(
            name=d.name,
            type=category,
            file=rel_path,
            line=d.line,
            syntactic_kind=d.syntactic_kind,
            signature=d.signature,
        )

    def classify(self, d: RawDefinition, rel_path: str) -> str | None:
        blob = " ".join(d.decorators)
        for rx, cat in DECORATOR_CAT:
            if rx.search(blob) or rx.search(d.signature):
                return cat
        for rx, cat in BASE_HINTS:
            if rx.search(d.signature):
                return cat
        rp = rel_path.lower()
        for rx, cat in PATH_CAT:
            if rx.search(rp):
                return cat
        if d.syntactic_kind == "interface":
            return "interfaces"
        if d.syntactic_kind == "class":
            return "classes"
        if d.syntactic_kind == "function" and d.name[:1].isupper():
            return "classes"
        return None

    def _regex_definitions(self, path: str, lang: str) -> list[RawDefinition]:
        patterns = REGEX_PATTERNS.get(lang, [])
        lines = self.scanner.read_lines(path)
        out: list[RawDefinition] = []
        for idx, line in enumerate(lines):
            for rx, kind in patterns:
                m = rx.search(line)
                if not m:
                    continue
                context = lines[max(0, idx - 4) : idx + 1]
                decs = tuple(
                    ln.strip()
                    for ln in context
                    if ln.strip().startswith("@")
                )
                out.append(
                    RawDefinition(
                        name=m.group(1),
                        syntactic_kind=kind,
                        line=idx + 1,
                        signature=line.strip()[:160],
                        decorators=decs,
                    )
                )
                break
        return out

    @staticmethod
    def build_graph(items: list[InventoryItem]) -> dict:
        nodes = [
            {
                "id": item.node_id(),
                "name": item.name,
                "type": item.type,
                "file": item.file,
                "line": item.line,
            }
            for item in items
        ]
        edges: list[dict] = []
        by_file: dict[str, list[InventoryItem]] = {}
        for item in items:
            by_file.setdefault(item.file, []).append(item)

        for file_path, group in by_file.items():
            ids = [i.node_id() for i in group]
            for i, a in enumerate(ids):
                for b in ids[i + 1 :]:
                    edges.append(
                        {"source": a, "target": b, "relation": "same_file", "file": file_path}
                    )

        # Link artifacts that share a directory prefix (module proximity).
        dir_groups: dict[str, list[InventoryItem]] = {}
        for item in items:
            dir_groups.setdefault(os.path.dirname(item.file), []).append(item)
        for directory, group in dir_groups.items():
            if not directory or len(group) < 2:
                continue
            for i, a in enumerate(group):
                for b in group[i + 1 :]:
                    edges.append(
                        {
                            "source": a.node_id(),
                            "target": b.node_id(),
                            "relation": "same_directory",
                            "directory": directory,
                        }
                    )

        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

    def render_markdown(self, result: InventoryResult) -> str:
        sections: list[ReportSection] = []
        meta = ReportSection(
            title="Summary",
            body=self.report_gen.key_values(
                [
                    ("Repository", result.repo),
                    ("Parser mode", result.parser_mode),
                    ("Parsers", ", ".join(result.parsers_available) or "none (regex fallback)"),
                    ("Total artifacts", sum(result.counts.values())),
                ]
            ),
        )
        sections.append(meta)

        for cat in CATEGORIES:
            items = result.by_category.get(cat, [])
            if not items:
                continue
            rows = [[i.name, i.file, i.line] for i in items]
            sections.append(
                ReportSection(
                    title=cat.capitalize(),
                    body=self.report_gen.table(["Name", "File", "Line"], rows),
                )
            )

        return self.report_gen.generate(
            f"Inventory — {result.repo_name}",
            sections,
            footer=self.report_gen.timestamp_footer("inventory_agent"),
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="B1 inventory agent")
    ap.add_argument("repo", help="path to repository")
    ap.add_argument(
        "--workspace",
        default="workspace",
        help="workspace root (default: workspace)",
    )
    ap.add_argument("--output-dir", help="override B1_inventory output directory")
    args = ap.parse_args(argv)

    try:
        result = InventoryAgent(workspace_root=args.workspace).run(
            args.repo, output_dir=args.output_dir
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = args.output_dir or os.path.join(
        args.workspace, result.repo_name, "B1_inventory"
    )
    print(f"Inventory complete ({result.parser_mode})")
    print(f"  output : {os.path.abspath(out)}")
    print(f"  items  : {len(result.items)}")
    print(f"  parsers: {', '.join(result.parsers_available) or 'regex fallback'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
