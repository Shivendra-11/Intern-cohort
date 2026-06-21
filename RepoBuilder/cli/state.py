"""Persist last-analyzed repo and server PIDs."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cli.paths import PID_FILE, STATE_DIR


@dataclass
class PlatformState:
    repo_path: str
    repo_name: str
    dashboard_path: str
    workspace_dir: str
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    ui_host: str = "127.0.0.1"
    ui_port: int = 3000

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PlatformState:
        return cls(
            repo_path=data["repo_path"],
            repo_name=data["repo_name"],
            dashboard_path=data["dashboard_path"],
            workspace_dir=data["workspace_dir"],
            api_host=data.get("api_host", "127.0.0.1"),
            api_port=int(data.get("api_port", 8000)),
            ui_host=data.get("ui_host", "127.0.0.1"),
            ui_port=int(data.get("ui_port", 3000)),
        )


def save_state(state: PlatformState, state_dir: Path | None = None) -> None:
    base = state_dir or STATE_DIR
    base.mkdir(parents=True, exist_ok=True)
    path = base / "state.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state.to_dict(), fh, indent=2)
        fh.write("\n")


def load_state(state_dir: Path | None = None) -> PlatformState | None:
    path = (state_dir or STATE_DIR) / "state.json"
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return PlatformState.from_dict(json.load(fh))
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def save_pids(api_pid: int, ui_pid: int) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"api_pid": api_pid, "ui_pid": ui_pid}
    with open(PID_FILE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def load_pids() -> dict[str, Any]:
    if not PID_FILE.is_file():
        return {}
    try:
        with open(PID_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def clear_pids() -> None:
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
