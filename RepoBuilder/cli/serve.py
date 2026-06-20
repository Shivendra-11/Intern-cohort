"""Start API backend and Vite frontend."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import webbrowser
from typing import List, Optional, Tuple

from cli.paths import (
    API_HOST,
    API_PORT,
    DASHBOARD_DIR,
    UI_HOST,
    UI_PORT,
    UI_URL,
)
from cli.state import PlatformState, clear_pids, load_state, save_pids, save_state


def _ensure_dashboard_deps(log=print) -> None:
    node_modules = DASHBOARD_DIR / "node_modules"
    if node_modules.is_dir():
        return
    if not shutil.which("npm"):
        raise RuntimeError("npm not found — install Node.js to run the dashboard UI")
    log("  → npm install (first run)…")
    proc = subprocess.run(
        ["npm", "install"],
        cwd=str(DASHBOARD_DIR),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"npm install failed:\n{proc.stderr or proc.stdout}")


def start_servers(
    state: Optional[PlatformState] = None,
    *,
    open_browser: bool = False,
    log=print,
) -> Tuple[subprocess.Popen, subprocess.Popen]:
    from cli.paths import WORKSPACE_ROOT

    state = state or load_state()
    if state is None and not WORKSPACE_ROOT.is_dir():
        raise FileNotFoundError(
            "No analyzed repositories found.\n"
            "Run: repo-intelligence analyze <repo>"
        )

    _ensure_dashboard_deps(log)

    env = os.environ.copy()
    env["REPOBUILDER_WORKSPACE"] = str(WORKSPACE_ROOT)
    if state:
        env["REPOBUILDER_DEFAULT_REPO"] = state.repo_name

    log("")
    log("Starting servers")
    log("-" * 40)

    api_cmd = [
        sys.executable,
        "-m",
        "core.api_server",
        "--workspace",
        str(WORKSPACE_ROOT),
        "--host",
        API_HOST,
        "--port",
        str(API_PORT),
    ]
    if state:
        api_cmd.extend(["--default-repo", state.repo_name])

    log(f"  API       : {API_HOST}:{API_PORT}")
    log(f"  UI        : {UI_URL}")
    log(f"  workspace : {WORKSPACE_ROOT}")
    if state:
        log(f"  default   : {state.repo_name}")
    log("")

    api_proc = subprocess.Popen(
        api_cmd,
        cwd=str(DASHBOARD_DIR.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    ui_cmd = ["npm", "run", "dev", "--", "--host", UI_HOST, "--port", str(UI_PORT)]
    ui_proc = subprocess.Popen(
        ui_cmd,
        cwd=str(DASHBOARD_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    save_pids(api_proc.pid, ui_proc.pid)
    if state:
        save_state(state)

    _wait_for_url(f"http://{API_HOST}:{API_PORT}/repos", timeout=30, log=log)
    _wait_for_url(UI_URL, timeout=60, log=log)

    if open_browser:
        webbrowser.open(UI_URL)
        log(f"  opened browser → {UI_URL}")

    log("")
    log(f"Dashboard ready at {UI_URL}")
    log("Press Ctrl+C to stop.")
    log("")

    return api_proc, ui_proc


def _wait_for_url(url: str, timeout: float = 30, log=print) -> None:
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except (urllib.error.URLError, OSError, TimeoutError):
            time.sleep(0.5)
    log(f"  warning: timed out waiting for {url}")


def run_serve(
    *,
    open_browser: bool = False,
    state: Optional[PlatformState] = None,
) -> int:
    state = state or load_state()
    if state is None:
        from cli.paths import WORKSPACE_ROOT
        from core.workspace_registry import WorkspaceRegistry

        registry = WorkspaceRegistry(str(WORKSPACE_ROOT))
        if not registry.list_repos():
            print(
                "No analyzed repo found. Run:\n"
                "  repo-intelligence analyze <repo>",
                file=sys.stderr,
            )
            return 2

    procs: List[subprocess.Popen] = []

    def shutdown(*_args) -> None:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        clear_pids()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        api_proc, ui_proc = start_servers(state, open_browser=open_browser)
        procs.extend([api_proc, ui_proc])
        while True:
            for p in procs:
                if p.poll() is not None:
                    out = p.stdout.read() if p.stdout else ""
                    print(out, file=sys.stderr)
                    return 1 if p.returncode else 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()
        return 0
