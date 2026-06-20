#!/usr/bin/env python3
"""B1 — Repo artifact inventory.

Walks a repository and classifies code artifacts into the categories an engineer
asks for during onboarding:

  classes, interfaces, services, controllers, models, repositories,
  jobs, consumers, configs, utilities  (+ a "components" bucket for frontend)

Heuristics combine framework decorators/annotations, base classes, and path/name
conventions. Stdlib-only, regex-based — fast and dependency-free, best-effort by
design (it favours recall; unknown stacks degrade to path heuristics).

Usage:
  python3 inventory.py <repo_path> [--json] [--limit N]

Default output is a human table; --json emits the full structured result.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import detect  # noqa: E402

CATEGORIES = [
    "classes", "interfaces", "services", "controllers", "models",
    "repositories", "jobs", "consumers", "configs", "utilities", "components",
]

# --- definition patterns: capture (name, kind) per language ------------------
DEF_PATTERNS = {
    "python": [
        (re.compile(r"^\s*class\s+(\w+)\s*(\([^)]*\))?"), "class"),
        (re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\("), "func"),
    ],
    "javascript": [
        (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("), "func"),
        (re.compile(r"^\s*(?:export\s+)?const\s+([A-Z]\w+)\s*=\s*(?:async\s*)?\("), "const_comp"),
    ],
    "typescript": [
        (re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:export\s+)?interface\s+(\w+)"), "interface"),
        (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("), "func"),
        (re.compile(r"^\s*(?:export\s+)?const\s+([A-Z]\w+)\s*[:=]"), "const_comp"),
    ],
    "java": [
        (re.compile(r"\b(?:public|private|protected)?\s*(?:abstract\s+|final\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"\binterface\s+(\w+)"), "interface"),
        (re.compile(r"\b(?:public\s+)?enum\s+(\w+)"), "class"),
    ],
    "kotlin": [
        (re.compile(r"\b(?:data\s+|sealed\s+|abstract\s+)?class\s+(\w+)"), "class"),
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

# Decorators / annotations that pin a definition to a category (any language).
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

# Base-class / signature hints (checked on the definition line itself).
BASE_HINTS = [
    (re.compile(r"\b(BaseModel|models\.Model|declarative_base|Base)\b"), "models"),
    (re.compile(r"\(\s*Protocol\s*\)|\(\s*ABC\s*\)|\(\s*ABCMeta\b"), "interfaces"),
]

# Path/name conventions -> category (substring match on relative path, lowercased).
PATH_CAT = [
    (re.compile(r"(^|/)(controllers?)(/|$)|controller\.\w+$"), "controllers"),
    (re.compile(r"(^|/)(services?)(/|$)|service\.\w+$"), "services"),
    (re.compile(r"(^|/)(repositor(y|ies))(/|$)|repository\.\w+$"), "repositories"),
    (re.compile(r"(^|/)(models?|entities|schemas?)(/|$)|model\.\w+$"), "models"),
    (re.compile(r"(^|/)(jobs?|tasks?|workers?)(/|$)|(job|worker)\.\w+$"), "jobs"),
    (re.compile(r"(^|/)(consumers?|listeners?|subscribers?)(/|$)|consumer\.\w+$"), "consumers"),
    (re.compile(r"(^|/)(utils?|helpers?|common|lib)(/|$)|(util|helper)s?\.\w+$"), "utilities"),
]


def category_for_def(name, kind, sig_line, context, rel_path):
    """Pick the most specific category for one definition."""
    blob = "\n".join(context)
    for rx, cat in DECORATOR_CAT:
        if rx.search(blob):
            return cat
    for rx, cat in BASE_HINTS:
        if rx.search(sig_line):
            return cat
    if kind == "interface":
        return "interfaces"
    if kind == "const_comp":
        return "components"
    rp = rel_path.lower()
    for rx, cat in PATH_CAT:
        if rx.search(rp):
            return cat
    # Frontend component file with a PascalCase export.
    if rel_path.endswith((".tsx", ".jsx")) and kind in ("func", "class") and name[:1].isupper():
        return "components"
    if kind == "class":
        return "classes"
    return None  # plain functions are not inventoried as artifacts


def scan_file(path, lang, root, result):
    rel_path = detect.rel(path, root)
    lines = detect.read_lines(path)
    patterns = DEF_PATTERNS.get(lang, [])
    for idx, line in enumerate(lines):
        for rx, kind in patterns:
            m = rx.search(line)
            if not m:
                continue
            name = m.group(1)
            # Look back up to 4 lines for decorators/annotations.
            context = lines[max(0, idx - 4): idx + 1]
            cat = category_for_def(name, kind, line, context, rel_path)
            if cat is None:
                break
            result[cat].append({
                "name": name,
                "file": rel_path,
                "line": idx + 1,
                "signature": line.strip()[:120],
            })
            break  # one definition kind per line


def scan_configs_and_utils(root, result):
    """File-level categorisation that doesn't need a definition (configs)."""
    for path in detect.walk_files(root):
        rel_path = detect.rel(path, root)
        if detect.is_config(path):
            result["configs"].append({
                "name": os.path.basename(path),
                "file": rel_path,
                "line": 1,
                "signature": "(config file)",
            })


def build_inventory(root):
    result = {c: [] for c in CATEGORIES}
    for path, lang in detect.source_files(root):
        scan_file(path, lang, root, result)
    scan_configs_and_utils(root, result)
    # De-duplicate by (name, file, line).
    for cat in result:
        seen = set()
        unique = []
        for item in result[cat]:
            key = (item["name"], item["file"], item["line"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        result[cat] = sorted(unique, key=lambda x: (x["file"], x["line"]))
    return result


def print_table(result, limit):
    counts = {c: len(result[c]) for c in CATEGORIES}
    total = sum(counts.values())
    print(f"Artifact inventory — {total} items across {sum(1 for c in counts if counts[c])} categories\n")
    for cat in CATEGORIES:
        items = result[cat]
        if not items:
            continue
        print(f"## {cat}  ({len(items)})")
        for item in items[:limit]:
            print(f"  {item['file']}:{item['line']}  {item['name']}")
        if len(items) > limit:
            print(f"  ... and {len(items) - limit} more")
        print()


def main(argv=None):
    ap = argparse.ArgumentParser(description="B1 repo artifact inventory")
    ap.add_argument("repo", help="path to the repository to scan")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    ap.add_argument("--limit", type=int, default=25, help="max items shown per category in table mode")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.repo):
        print(f"error: not a directory: {args.repo}", file=sys.stderr)
        return 2

    result = build_inventory(args.repo)
    if args.json:
        print(json.dumps({
            "repo": os.path.abspath(args.repo),
            "counts": {c: len(result[c]) for c in CATEGORIES},
            "artifacts": result,
        }, indent=2))
    else:
        print_table(result, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
