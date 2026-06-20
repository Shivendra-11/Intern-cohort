"""Start the ParallelOps eval dashboard (Vite dev server)."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def dashboard_dir(repo_root: Path) -> Path:
    return repo_root / ".parallelops" / "dashboard"


def port_file(repo_root: Path) -> Path:
    return repo_root / ".parallelops" / "dashboard.port"


def _npm_available() -> bool:
    return shutil.which("npm") is not None


def is_port_in_use(port: int, host: str = "localhost") -> bool:
    try:
        candidates = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for family, _, _, _, sockaddr in candidates:
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.3)
                if sock.connect_ex(sockaddr) == 0:
                    return True
        except OSError:
            continue
    return False


def fetch_dashboard_repo_root(port: int, host: str = "localhost") -> str | None:
    """Return repo_root served by an existing dashboard on ``port``, if any."""
    url = f"http://{host}:{port}/api/artifacts/index.json"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    repo_root = data.get("repo_root")
    return str(repo_root) if repo_root else None


def resolve_dashboard_port(
    repo_root: Path,
    *,
    preferred: int = 3000,
    max_scan: int = 20,
) -> int:
    """
    Pick a port for this repo's dashboard.

    Reuses a stored port when it still serves this repo; otherwise scans upward
    from ``preferred`` for a free port or one already bound to the same repo.
    """
    resolved = repo_root.resolve()
    stored = port_file(repo_root)
    if stored.exists():
        try:
            saved_port = int(stored.read_text(encoding="utf-8").strip())
            if not is_port_in_use(saved_port):
                return saved_port
            existing = fetch_dashboard_repo_root(saved_port)
            if existing and Path(existing).resolve() == resolved:
                return saved_port
        except ValueError:
            pass

    for offset in range(max_scan):
        candidate = preferred + offset
        if not is_port_in_use(candidate):
            return candidate
        existing = fetch_dashboard_repo_root(candidate)
        if existing and Path(existing).resolve() == resolved:
            return candidate

    raise RuntimeError(
        f"No available dashboard port found for {resolved.name} "
        f"(checked {preferred}–{preferred + max_scan - 1})"
    )


def ensure_dashboard_deps(repo_root: Path) -> None:
    dash = dashboard_dir(repo_root)
    if not (dash / "package.json").exists():
        raise FileNotFoundError(f"Dashboard not found at {dash}")
    node_modules = dash / "node_modules"
    if not node_modules.exists():
        subprocess.run(["npm", "install"], cwd=dash, check=True)


def start_dashboard(
    repo_root: Path,
    *,
    port: int = 3000,
    open_browser: bool = False,
    session_id: str | None = None,
) -> subprocess.Popen[str]:
    """Start Vite dev server; returns subprocess handle."""
    if not _npm_available():
        raise RuntimeError("npm is required to run the eval dashboard")

    dash = dashboard_dir(repo_root)
    ensure_dashboard_deps(repo_root)

    env = os.environ.copy()
    env["VITE_ARTIFACTS_ROOT"] = str((repo_root / ".parallelops" / "artifacts").resolve())
    if session_id:
        env["VITE_DEFAULT_SESSION"] = session_id

    log_path = repo_root / ".parallelops" / "dashboard.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "a", encoding="utf-8")

    cmd = ["npm", "run", "dev", "--", "--port", str(port), "--strictPort"]
    if not open_browser:
        cmd.append("--open=false")

    proc = subprocess.Popen(
        cmd,
        cwd=dash,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(2.0)
    return proc


def dashboard_url(port: int = 3000, session_id: str | None = None) -> str:
    base = f"http://localhost:{port}"
    if session_id:
        return f"{base}/?session={session_id}"
    return base


def _write_port_file(repo_root: Path, port: int) -> None:
    port_file(repo_root).write_text(f"{port}\n", encoding="utf-8")


def ensure_dashboard_running(
    repo_root: Path,
    *,
    port: int = 3000,
    session_id: str | None = None,
    foreground: bool = False,
) -> dict[str, object]:
    """Start dashboard if needed; return URL metadata (non-blocking unless foreground)."""
    resolved_port = resolve_dashboard_port(repo_root, preferred=port)
    url = dashboard_url(resolved_port, session_id)
    repo_name = repo_root.resolve().name

    if foreground:
        run_dashboard_foreground(
            repo_root,
            port=resolved_port,
            session_id=session_id,
        )
        return {
            "dashboard_url": url,
            "dashboard_running": True,
            "mode": "foreground",
            "port": resolved_port,
            "repo_name": repo_name,
        }

    if is_port_in_use(resolved_port):
        existing = fetch_dashboard_repo_root(resolved_port)
        if existing and Path(existing).resolve() == repo_root.resolve():
            _write_port_file(repo_root, resolved_port)
            return {
                "dashboard_url": url,
                "dashboard_running": True,
                "already_running": True,
                "port": resolved_port,
                "repo_name": repo_name,
            }

    proc = start_dashboard(
        repo_root,
        port=resolved_port,
        open_browser=False,
        session_id=session_id,
    )
    pid_path = repo_root / ".parallelops" / "dashboard.pid"
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    _write_port_file(repo_root, resolved_port)
    return {
        "dashboard_url": url,
        "dashboard_running": True,
        "pid": proc.pid,
        "port": resolved_port,
        "repo_name": repo_name,
        "log": str(repo_root / ".parallelops" / "dashboard.log"),
    }


def run_dashboard_foreground(
    repo_root: Path,
    *,
    port: int = 3000,
    session_id: str | None = None,
) -> int:
    resolved_port = resolve_dashboard_port(repo_root, preferred=port)
    url = dashboard_url(resolved_port, session_id)
    repo_name = repo_root.resolve().name

    if is_port_in_use(resolved_port):
        existing = fetch_dashboard_repo_root(resolved_port)
        if existing and Path(existing).resolve() == repo_root.resolve():
            print(
                f"\n{repo_name} eval dashboard already running on port {resolved_port}\n  {url}\n"
            )
            _write_port_file(repo_root, resolved_port)
            return 0

    proc = start_dashboard(
        repo_root,
        port=resolved_port,
        open_browser=False,
        session_id=session_id,
    )
    _write_port_file(repo_root, resolved_port)
    print(f"\n{repo_name} Eval Dashboard\n  {url}\n\nPress Ctrl+C to stop.\n")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait(timeout=5)
    return 0
