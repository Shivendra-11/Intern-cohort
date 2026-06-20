"""Approval gate state for A2 execution and merge to main."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def save_approval(repo_root: Path, session_id: str, artifact_location: str = ".parallelops/artifacts") -> Path:
    path = repo_root / artifact_location / "execution_approved.json"
    path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "approved": True,
                "approved_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def is_approved(repo_root: Path, session_id: str, artifact_location: str = ".parallelops/artifacts") -> bool:
    path = repo_root / artifact_location / "execution_approved.json"
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("approved") is True and data.get("session_id") == session_id


def save_merge_approval(
    repo_root: Path, session_id: str, artifact_location: str = ".parallelops/artifacts"
) -> Path:
    path = repo_root / artifact_location / "merge_approved.json"
    path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "merge_approved": True,
                "approved_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def is_merge_approved(
    repo_root: Path, session_id: str, artifact_location: str = ".parallelops/artifacts"
) -> bool:
    path = repo_root / artifact_location / "merge_approved.json"
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("merge_approved") is True and data.get("session_id") == session_id
