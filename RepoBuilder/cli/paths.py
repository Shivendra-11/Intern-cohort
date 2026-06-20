"""Platform paths and constants."""
from __future__ import annotations

import os
from pathlib import Path

PLATFORM_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PLATFORM_ROOT / "workspace"
DASHBOARD_DIR = PLATFORM_ROOT / "dashboard"
STATE_DIR = WORKSPACE_ROOT / ".repo-intelligence"
STATE_FILE = STATE_DIR / "state.json"
PID_FILE = STATE_DIR / "pids.json"

API_HOST = "127.0.0.1"
API_PORT = 8000
UI_HOST = "127.0.0.1"
UI_PORT = 3000

UI_URL = f"http://{UI_HOST}:{UI_PORT}"
API_URL = f"http://{API_HOST}:{API_PORT}"


def workspace_for_repo(repo_path: str) -> Path:
    name = os.path.basename(os.path.abspath(repo_path).rstrip(os.sep)) or "repository"
    return WORKSPACE_ROOT / name


def dashboard_path_for_repo(repo_path: str) -> Path:
    return workspace_for_repo(repo_path) / "dashboard_data.json"
