"""FastAPI server exposing dashboard_data.json for the Repo Intelligence UI."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.workspace_registry import WorkspaceRegistry

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class DashboardNotLoadedError(Exception):
    """Raised when no repository dashboard is available."""


class DashboardStore:
    """Load and serve sections from one repository dashboard_data.json."""

    def __init__(self, path: str, repo_id: str) -> None:
        self.path = os.path.abspath(path)
        self.repo_id = repo_id
        self._data: Optional[Dict[str, Any]] = None
        self.reload()

    def reload(self) -> None:
        if not os.path.isfile(self.path):
            self._data = None
            return
        try:
            import json

            with open(self.path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            self._data = None

    @property
    def loaded(self) -> bool:
        return self._data is not None

    def require_loaded(self) -> Dict[str, Any]:
        if not self.loaded or self._data is None:
            raise DashboardNotLoadedError(
                f"dashboard not loaded for repo '{self.repo_id}': {self.path}"
            )
        return self._data

    def section(self, key: str) -> Any:
        data = self.require_loaded()
        return data.get(key)

    def overview(self) -> dict:
        data = self.require_loaded()
        return {
            "repo_id": self.repo_id,
            "schema_version": data.get("schema_version"),
            "role": data.get("role"),
            "repo": data.get("repo"),
            "repo_name": data.get("repo_name"),
            "repo_path": data.get("repo_path"),
            "workspace_dir": data.get("workspace_dir"),
            "generated_at": data.get("generated_at"),
            "sources": data.get("sources"),
            "summary": data.get("summary"),
        }


def default_workspace_root() -> str:
    env = os.environ.get("REPOBUILDER_WORKSPACE")
    if env:
        return os.path.abspath(env)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "workspace")


def default_repo_name() -> Optional[str]:
    env = os.environ.get("REPOBUILDER_DEFAULT_REPO")
    if env:
        return env
    legacy = os.environ.get("REPOBUILDER_DASHBOARD_PATH")
    if legacy and os.path.isfile(legacy):
        return os.path.basename(os.path.dirname(os.path.abspath(legacy)))
    return None


def create_app(
    workspace_root: Optional[str] = None,
    dashboard_path: Optional[str] = None,
    default_repo: Optional[str] = None,
) -> FastAPI:
    ws = workspace_root or default_workspace_root()
    if dashboard_path and not workspace_root:
        dashboard_path = os.path.abspath(dashboard_path)
        ws = os.path.dirname(os.path.dirname(dashboard_path))
        default_repo = default_repo or os.path.basename(
            os.path.dirname(dashboard_path)
        )

    registry = WorkspaceRegistry(ws, default_repo=default_repo or default_repo_name())

    app = FastAPI(
        title="Repo Intelligence Dashboard API",
        version="1.1.0",
        description="Multi-repo read-only API backed by workspace/*/dashboard_data.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    def _store(repo: Optional[str] = None) -> DashboardStore:
        try:
            path = registry.dashboard_path_for(repo)
        except FileNotFoundError as exc:
            raise DashboardNotLoadedError(str(exc)) from exc
        rid = repo or registry.resolve_default_repo() or "unknown"
        return DashboardStore(path, repo_id=rid)

    @app.exception_handler(DashboardNotLoadedError)
    def _dashboard_missing(_request, exc: DashboardNotLoadedError):
        return JSONResponse(
            status_code=503,
            content={
                "detail": str(exc),
                "workspace": registry.workspace_root,
            },
        )

    @app.get("/repos")
    def list_repos() -> dict:
        repos = registry.list_repos()
        default = registry.resolve_default_repo()
        return {
            "workspace": registry.workspace_root,
            "default": default,
            "count": len(repos),
            "repos": [r.to_dict() for r in repos],
        }

    @app.get("/overview")
    def get_overview(repo: Optional[str] = Query(None, description="workspace repo id")) -> dict:
        return _store(repo).overview()

    @app.get("/inventory")
    def get_inventory(repo: Optional[str] = Query(None)) -> Any:
        data = _store(repo).section("inventory")
        if data is None:
            raise HTTPException(status_code=404, detail="inventory not available")
        return data

    @app.get("/routes")
    def get_routes(repo: Optional[str] = Query(None)) -> Any:
        data = _store(repo).section("routes")
        if data is None:
            raise HTTPException(status_code=404, detail="routes not available")
        return data

    @app.get("/tests")
    def get_tests(repo: Optional[str] = Query(None)) -> Any:
        data = _store(repo).section("tests")
        if data is None:
            raise HTTPException(status_code=404, detail="tests not available")
        return data

    @app.get("/graphs")
    def get_graphs(repo: Optional[str] = Query(None)) -> Any:
        data = _store(repo).section("graphs")
        if data is None:
            raise HTTPException(status_code=404, detail="graphs not available")
        return data

    @app.get("/projects")
    def get_projects(repo: Optional[str] = Query(None)) -> Any:
        data = _store(repo).section("generated_projects")
        if data is None:
            raise HTTPException(status_code=404, detail="projects not available")
        return data

    app.state.registry = registry
    return app


app = create_app()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run dashboard API on localhost:8000")
    ap.add_argument(
        "--workspace",
        help="workspace root (default: REPOBUILDER_WORKSPACE or ./workspace)",
    )
    ap.add_argument(
        "--dashboard",
        help="legacy: path to one dashboard_data.json (infers workspace + default repo)",
    )
    ap.add_argument(
        "--default-repo",
        help="default repository id under workspace/",
    )
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = ap.parse_args(argv)

    try:
        import uvicorn
    except ImportError:
        print("error: uvicorn not installed — pip install -r requirements-api.txt", file=sys.stderr)
        return 2

    global app
    app = create_app(
        workspace_root=args.workspace,
        dashboard_path=args.dashboard,
        default_repo=args.default_repo,
    )

    registry: WorkspaceRegistry = app.state.registry
    repos = registry.list_repos()
    if not repos:
        print(f"warning: no repos found under {registry.workspace_root}", file=sys.stderr)

    print(f"Dashboard API http://{args.host}:{args.port}")
    print(f"  workspace : {registry.workspace_root}")
    print(f"  repos     : {len(repos)} ({', '.join(r.id for r in repos) or 'none'})")
    if registry.resolve_default_repo():
        print(f"  default   : {registry.resolve_default_repo()}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
