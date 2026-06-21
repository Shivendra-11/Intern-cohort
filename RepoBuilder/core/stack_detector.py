"""Detect primary technology stacks in a repository (Node, Python, Java, Rust, Go)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from core.file_scanner import FileScanner, ScanResult

# Stack name → manifest filenames that prove presence (checked at repo root first, then anywhere).
STACK_MARKERS: dict[str, list[str]] = {
    "node": ["package.json"],
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"],
    "rust": ["Cargo.toml"],
    "go": ["go.mod"],
}

# Map scanner language labels → platform stack names.
LANG_TO_STACK: dict[str, str] = {
    "javascript": "node",
    "typescript": "node",
    "python": "python",
    "java": "java",
    "kotlin": "java",
    "rust": "rust",
    "go": "go",
}


@dataclass(frozen=True)
class DetectedStack:
    """One detected technology stack with evidence."""

    name: str  # node | python | java | rust | go
    manifest: str | None  # relative path to primary manifest, if found
    source_file_count: int
    confidence: str  # high | medium | low


@dataclass
class StackProfile:
    """Full stack detection result for a repository."""

    root: str
    stacks: list[DetectedStack] = field(default_factory=list)
    primary_stack: str | None = None
    languages: dict[str, int] = field(default_factory=dict)
    manifests: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "primary_stack": self.primary_stack,
            "stacks": [
                {
                    "name": s.name,
                    "manifest": s.manifest,
                    "source_file_count": s.source_file_count,
                    "confidence": s.confidence,
                }
                for s in self.stacks
            ],
            "languages": self.languages,
            "manifests": self.manifests,
        }


class StackDetector:
    """Identify Node, Python, Java, Rust, and Go stacks from filesystem signals."""

    SUPPORTED_STACKS: set[str] = {"node", "python", "java", "rust", "go"}

    def __init__(self, scanner: FileScanner | None = None) -> None:
        self.scanner = scanner or FileScanner()

    def detect(self, root: str, scan: ScanResult | None = None) -> StackProfile:
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            raise ValueError(f"not a directory: {root}")

        scan = scan or self.scanner.scan(root)
        manifests = self._find_manifests(root, scan)
        lang_counts = self._language_counts(scan)
        stack_source_counts = self._stack_source_counts(lang_counts)

        detected: list[DetectedStack] = []
        for stack_name in sorted(self.SUPPORTED_STACKS):
            manifest = manifests.get(stack_name)
            count = stack_source_counts.get(stack_name, 0)
            if manifest or count > 0:
                confidence = self._confidence(manifest, count)
                detected.append(
                    DetectedStack(
                        name=stack_name,
                        manifest=manifest,
                        source_file_count=count,
                        confidence=confidence,
                    )
                )

        detected.sort(key=lambda s: (-s.source_file_count, s.name))
        primary = detected[0].name if detected else None

        return StackProfile(
            root=root,
            stacks=detected,
            primary_stack=primary,
            languages=lang_counts,
            manifests={k: v for k, v in manifests.items() if v},
        )

    def _find_manifests(self, root: str, scan: ScanResult) -> dict[str, str | None]:
        found: dict[str, str | None] = {s: None for s in self.SUPPORTED_STACKS}

        # Prefer manifests at repository root.
        for stack, names in STACK_MARKERS.items():
            for name in names:
                root_path = os.path.join(root, name)
                if os.path.isfile(root_path):
                    found[stack] = name
                    break

        # Fall back to nested manifests (monorepo layouts).
        rel_paths = {f.relative_path.replace("\\", "/") for f in scan.files}
        for stack, names in STACK_MARKERS.items():
            if found[stack]:
                continue
            for rel in sorted(rel_paths):
                base = os.path.basename(rel)
                if base in names:
                    found[stack] = rel
                    break

        return found

    @staticmethod
    def _language_counts(scan: ScanResult) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rec in scan.source_files:
            if rec.language:
                counts[rec.language] = counts.get(rec.language, 0) + 1
        return counts

    @staticmethod
    def _stack_source_counts(lang_counts: dict[str, int]) -> dict[str, int]:
        totals: dict[str, int] = {s: 0 for s in STACK_MARKERS}
        for lang, count in lang_counts.items():
            stack = LANG_TO_STACK.get(lang)
            if stack:
                totals[stack] = totals.get(stack, 0) + count
        return totals

    @staticmethod
    def _confidence(manifest: str | None, source_count: int) -> str:
        if manifest and source_count > 0:
            return "high"
        if manifest or source_count >= 5:
            return "medium"
        return "low"
