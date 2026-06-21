"""Run B1–B6 pipeline and build dashboard_data.json."""
from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from core.dashboard_data_builder import DashboardDataBuilder
from core.fastapi_builder import FastAPIBuilder
from core.graph_engine import GraphEngine
from core.inventory_agent import InventoryAgent
from core.node_builder import NodeBuilder
from core.route_agent import RouteAgent
from core.rust_builder import RustBuilder
from core.test_agent import TestAgent

from cli.paths import WORKSPACE_ROOT
from cli.state import PlatformState, save_state


@dataclass
class StepResult:
    name: str
    status: str
    detail: str = ""
    duration_ms: int = 0


@dataclass
class AnalyzeResult:
    repo_path: str
    repo_name: str
    workspace_dir: str
    dashboard_path: str
    steps: list[StepResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(s.status in ("OK", "SKIPPED") for s in self.steps)


def _step(name: str, fn: Callable[[], None], log: Callable[[str], None]) -> StepResult:
    log(f"  → {name}")
    t0 = time.monotonic()
    try:
        fn()
        ms = int((time.monotonic() - t0) * 1000)
        log(f"    ✓ {name} ({ms}ms)")
        return StepResult(name=name, status="OK", duration_ms=ms)
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        log(f"    ✗ {name}: {exc}")
        return StepResult(name=name, status="FAILED", detail=str(exc), duration_ms=ms)


def run_analyze(
    repo_path: str,
    *,
    workspace_root: str | None = None,
    run_tests: bool = True,
    builder_proof: bool = False,
    log: Callable[[str], None] | None = None,
) -> AnalyzeResult:
    repo_path = os.path.abspath(repo_path)
    if not os.path.isdir(repo_path):
        raise ValueError(f"not a directory: {repo_path}")

    ws = workspace_root or str(WORKSPACE_ROOT)
    repo_name = os.path.basename(repo_path.rstrip(os.sep)) or "repository"
    out = log or print

    out("")
    out("Repo Intelligence — analyze pipeline")
    out("=" * 40)
    out(f"  repo      : {repo_path}")
    out(f"  workspace : {os.path.join(ws, repo_name)}")
    out("")

    steps: list[StepResult] = []

    steps.append(_step("B1 inventory", lambda: InventoryAgent(workspace_root=ws).run(repo_path), out))
    steps.append(_step("B2 routes", lambda: RouteAgent(workspace_root=ws).run(repo_path), out))
    steps.append(
        _step(
            "B3 tests",
            lambda: TestAgent(workspace_root=ws).run(
                repo_path, execute=run_tests
            ),
            out,
        )
    )
    steps.append(
        _step(
            "Graph engine",
            lambda: GraphEngine().write_graph_data(repo_path, workspace_root=ws),
            out,
        )
    )
    steps.append(
        _step(
            "B4 FastAPI greenfield",
            lambda: FastAPIBuilder(workspace_root=ws).build(
                repo_path, run_proof=builder_proof
            ),
            out,
        )
    )
    steps.append(
        _step(
            "B5 Node greenfield",
            lambda: NodeBuilder(workspace_root=ws).build(
                repo_path, run_proof=builder_proof
            ),
            out,
        )
    )
    steps.append(
        _step(
            "B6 Rust greenfield",
            lambda: RustBuilder(workspace_root=ws).build(
                repo_path, run_proof=builder_proof
            ),
            out,
        )
    )

    dashboard_path = os.path.join(ws, repo_name, "dashboard_data.json")
    workspace_dir = os.path.join(ws, repo_name)

    def build_dashboard() -> None:
        result = DashboardDataBuilder(workspace_root=ws).build(repo_path)
        if not os.path.isfile(result.output_path):
            raise RuntimeError("dashboard_data.json not written")

    steps.append(_step("dashboard_data.json", build_dashboard, out))

    save_state(
        PlatformState(
            repo_path=repo_path,
            repo_name=repo_name,
            dashboard_path=dashboard_path,
            workspace_dir=workspace_dir,
        ),
        state_dir=Path(ws) / ".repo-intelligence",
    )

    out("")
    out("Pipeline summary")
    out("-" * 40)
    for s in steps:
        mark = "✓" if s.status == "OK" else ("○" if s.status == "SKIPPED" else "✗")
        out(f"  {mark} {s.name:<22} {s.status:<8} {s.duration_ms:>5}ms")
    out("")
    out(f"  dashboard_data.json → {dashboard_path}")
    out("")

    return AnalyzeResult(
        repo_path=repo_path,
        repo_name=repo_name,
        workspace_dir=workspace_dir,
        dashboard_path=dashboard_path,
        steps=steps,
    )
