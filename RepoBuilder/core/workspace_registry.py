"""Discover analyzed repositories under workspace/."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RepoEntry:
    id: str
    repo_name: str
    repo_path: str
    workspace_dir: str
    dashboard_path: str
    generated_at: str = ""
    status: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repo_name": self.repo_name,
            "repo_path": self.repo_path,
            "workspace_dir": self.workspace_dir,
            "dashboard_path": self.dashboard_path,
            "generated_at": self.generated_at,
            "status": self.status,
        }


class WorkspaceRegistry:
    """Map workspace/{repo_id}/ → dashboard_data.json per repository."""

    DASHBOARD_FILE = "dashboard_data.json"
    STATE_REL = os.path.join(".repo-intelligence", "state.json")

    def __init__(
        self,
        workspace_root: str,
        *,
        default_repo: Optional[str] = None,
    ) -> None:
        self.workspace_root = os.path.abspath(workspace_root)
        self.default_repo = default_repo

    def list_repos(self) -> List[RepoEntry]:
        entries: List[RepoEntry] = []
        if not os.path.isdir(self.workspace_root):
            return entries

        for name in sorted(os.listdir(self.workspace_root)):
            if name.startswith("."):
                continue
            ws_dir = os.path.join(self.workspace_root, name)
            if not os.path.isdir(ws_dir):
                continue
            dashboard = os.path.join(ws_dir, self.DASHBOARD_FILE)
            if not os.path.isfile(dashboard):
                continue
            entries.append(self._entry_from_file(name, ws_dir, dashboard))

        return entries

    def _entry_from_file(self, repo_id: str, ws_dir: str, dashboard: str) -> RepoEntry:
        meta = self._read_dashboard_meta(dashboard)
        status = "complete"
        summary = meta.get("summary") or {}
        pipelines = summary.get("pipelines") or {}
        if pipelines:
            core_ok = all(
                pipelines.get(k) == "complete"
                for k in ("B1_inventory", "B2_routes", "B3_tests", "graphs")
            )
            status = "complete" if core_ok else "partial"

        return RepoEntry(
            id=repo_id,
            repo_name=meta.get("repo_name") or repo_id,
            repo_path=meta.get("repo_path") or "",
            workspace_dir=ws_dir,
            dashboard_path=dashboard,
            generated_at=(meta.get("generated_at") or "")[:19],
            status=status,
        )

    @staticmethod
    def _read_dashboard_meta(path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}

    def resolve_default_repo(self) -> Optional[str]:
        if self.default_repo and self._has_repo(self.default_repo):
            return self.default_repo

        state_path = os.path.join(self.workspace_root, self.STATE_REL)
        if os.path.isfile(state_path):
            try:
                with open(state_path, encoding="utf-8") as fh:
                    name = json.load(fh).get("repo_name")
                if name and self._has_repo(name):
                    return name
            except (OSError, json.JSONDecodeError, TypeError):
                pass

        repos = self.list_repos()
        return repos[0].id if repos else None

    def _has_repo(self, repo_id: str) -> bool:
        path = os.path.join(
            self.workspace_root, repo_id, self.DASHBOARD_FILE
        )
        return os.path.isfile(path)

    def dashboard_path_for(self, repo_id: Optional[str] = None) -> str:
        rid = repo_id or self.resolve_default_repo()
        if not rid:
            raise FileNotFoundError(
                f"no repositories with {self.DASHBOARD_FILE} under {self.workspace_root}"
            )
        path = os.path.join(self.workspace_root, rid, self.DASHBOARD_FILE)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"repository not found: {rid}")
        return path

    def load_dashboard(self, repo_id: Optional[str] = None) -> Dict[str, Any]:
        path = self.dashboard_path_for(repo_id)
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
