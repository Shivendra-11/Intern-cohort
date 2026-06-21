"""Recursively scan repository files with language and config classification."""
from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass, field

# Directories skipped during traversal (vendored deps, build output, VCS, caches).
IGNORE_DIRS: set[str] = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "target",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "out",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".gradle",
    "vendor",
    "coverage",
    ".cache",
    "site-packages",
    "bin",
    "obj",
}

# Extension → language label (stacks supported by the platform).
EXT_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".go": "go",
    ".rs": "rust",
}

CONFIG_NAMES: set[str] = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "makefile",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "requirements.txt",
    "pipfile",
    "package.json",
    "tsconfig.json",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
}

CONFIG_EXTS: set[str] = {".yml", ".yaml", ".toml", ".ini", ".cfg", ".env", ".properties"}


@dataclass(frozen=True)
class FileRecord:
    """A single file discovered under a repository root."""

    absolute_path: str
    relative_path: str
    language: str | None
    is_config: bool
    size_bytes: int


@dataclass
class ScanResult:
    """Aggregated output of a repository file scan."""

    root: str
    files: list[FileRecord] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def by_language(self) -> dict[str, list[FileRecord]]:
        out: dict[str, list[FileRecord]] = {}
        for rec in self.files:
            if rec.language:
                out.setdefault(rec.language, []).append(rec)
        return out

    @property
    def config_files(self) -> list[FileRecord]:
        return [f for f in self.files if f.is_config]

    @property
    def source_files(self) -> list[FileRecord]:
        return [f for f in self.files if f.language is not None]


class FileScanner:
    """Walk a repository tree and classify files by language and role."""

    def __init__(
        self,
        ignore_dirs: set[str] | None = None,
        max_file_bytes: int = 1_500_000,
    ) -> None:
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else set(IGNORE_DIRS)
        self.max_file_bytes = max_file_bytes

    def scan(self, root: str) -> ScanResult:
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            raise ValueError(f"not a directory: {root}")

        result = ScanResult(root=root)
        for abs_path in self.iter_files(root):
            rel = os.path.relpath(abs_path, root)
            try:
                size = os.path.getsize(abs_path)
            except OSError:
                size = 0
            result.files.append(
                FileRecord(
                    absolute_path=abs_path,
                    relative_path=rel,
                    language=self.language_of(abs_path),
                    is_config=self.is_config_file(abs_path),
                    size_bytes=size,
                )
            )
        return result

    def iter_files(self, root: str) -> Iterator[str]:
        """Yield absolute file paths under root, skipping ignored directories."""
        root = os.path.abspath(root)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d
                for d in dirnames
                if self._should_descend(d)
            ]
            for name in filenames:
                yield os.path.join(dirpath, name)

    def _should_descend(self, dirname: str) -> bool:
        low = dirname.lower()
        if low in self.ignore_dirs:
            return False
        if dirname.startswith(".") and dirname not in {".github"}:
            return False
        return True

    @staticmethod
    def language_of(path: str) -> str | None:
        _, ext = os.path.splitext(path)
        return EXT_LANG.get(ext.lower())

    @staticmethod
    def is_config_file(path: str) -> bool:
        base = os.path.basename(path).lower()
        if base in CONFIG_NAMES:
            return True
        _, ext = os.path.splitext(base)
        if ext in CONFIG_EXTS:
            return True
        return base.startswith("settings.") or "config" in base

    def read_lines(self, path: str) -> list[str]:
        """Read a text file as lines; return [] for unreadable or oversized files."""
        try:
            if os.path.getsize(path) > self.max_file_bytes:
                return []
            with open(path, encoding="utf-8", errors="ignore") as fh:
                return fh.read().splitlines()
        except (OSError, UnicodeDecodeError):
            return []

    def iter_source_files(
        self, root: str, languages: set[str] | None = None
    ) -> Iterator[tuple[str, str]]:
        """Yield (absolute_path, language) for source files, optionally filtered."""
        want = languages
        for path in self.iter_files(root):
            lang = self.language_of(path)
            if lang is None:
                continue
            if want and lang not in want:
                continue
            yield path, lang
