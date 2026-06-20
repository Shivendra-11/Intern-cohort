"""Write and read JSON files with atomic, validated persistence."""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Optional, Union


class JsonWriter:
    """Persist JSON documents to disk safely."""

    def __init__(self, indent: int = 2, ensure_ascii: bool = False) -> None:
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def write(self, path: str, data: Any) -> str:
        """Atomically write data as JSON. Returns the absolute path written."""
        path = os.path.abspath(path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        payload = json.dumps(
            data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            sort_keys=False,
        )
        # Validate round-trip before committing.
        json.loads(payload)

        directory = os.path.dirname(path) or "."
        fd, tmp_path = tempfile.mkstemp(prefix=".json-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.write("\n")
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        return path

    def write_if_changed(self, path: str, data: Any) -> bool:
        """Write only when content differs from existing file. Returns True if written."""
        path = os.path.abspath(path)
        new_payload = json.dumps(
            data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            sort_keys=True,
        )
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    existing = json.load(fh)
                old_payload = json.dumps(
                    existing,
                    indent=self.indent,
                    ensure_ascii=self.ensure_ascii,
                    sort_keys=True,
                )
                if old_payload == new_payload:
                    return False
            except (OSError, json.JSONDecodeError):
                pass
        self.write(path, data)
        return True


def read_json(path: str, default: Optional[Any] = None) -> Any:
    """Load JSON from path; return default if missing or invalid."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        if default is not None:
            return default
        raise
