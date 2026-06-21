"""Eval artifact writer — four-file bundle per agent + session index for dashboard."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from parallelops.models import new_session_id

EVAL_AGENTS = ("A1", "A2", "A3", "A4", "A5")
BATTERY_AGENTS = ("A1", "A2", "A3", "A4", "A5", "A6")
BATTERY_ORDER = ("A1", "A2", "A3", "A5", "A6", "A4")
ARTIFACT_FILES = ("metadata.json", "report.json", "report.md", "logs.txt")

# First existing path wins — used by dashboard-from-md mode
AGENT_MD_SOURCES: dict[str, tuple[str, ...]] = {
    "A1": (
        ".parallelops/artifacts/A1/report.md",
        "a1-worktree-plan/decomposition.md",
        "a1-worktree-plan/merge-plan.md",
    ),
    "A2": (
        ".parallelops/artifacts/A2/report.md",
        "a2-parallel-worktrees/RECONCILE.md",
    ),
    "A3": (
        ".parallelops/artifacts/A3/report.md",
        "a3-polyglot/README.md",
        "fraud-system/PROOF.md",
    ),
    "A4": (
        ".parallelops/artifacts/A4/report.md",
        "a4-modernization/FINDINGS.md",
        "a4-modernization/PROOF.md",
    ),
    "A5": (
        ".parallelops/artifacts/A5/report.md",
        "EVAL-REPORT.md",
    ),
    "A6": (
        ".parallelops/artifacts/A6/report.md",
        "a6-perf-profiling/PLAN.md",
    ),
}


@dataclass
class AgentResult:
    agent: str
    status: str = "pass"
    mode: str = "build+verify"
    summary: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: int | None = None
    report_md_path: str | None = None
    report_json_path: str | None = None
    logs_path: str | None = None
    charts: dict[str, Any] = field(default_factory=dict)
    chart_plan: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalSession:
    session_id: str
    task: str = ""
    mode: str = "build+verify"
    repo_root: str = ""
    started_at: str = ""
    finished_at: str | None = None
    agents: list[str] = field(default_factory=list)
    agent_results: dict[str, AgentResult] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_context(repo_root: Path | str) -> dict[str, str]:
    """Normalized repo path + short name for dashboard display."""
    path = Path(repo_root).resolve()
    return {
        "repo_root": str(path),
        "repo_name": path.name or str(path),
    }


def artifacts_root(repo_root: Path) -> Path:
    return repo_root / ".parallelops" / "artifacts"


def runs_root(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "runs"


def run_dir(repo_root: Path, session_id: str) -> Path:
    return runs_root(repo_root) / session_id


def agent_dir(repo_root: Path, session_id: str, agent: str) -> Path:
    return run_dir(repo_root, session_id) / agent


def session_file(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "eval_session.json"


def selection_file(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "eval_selection.json"


def results_file(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "eval_results.json"


def index_file(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "index.json"


def dashboard_manifest_file(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "dashboard.json"


def dashboard_url_file(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "dashboard_url.txt"


def repo_context_file(repo_root: Path) -> Path:
    return artifacts_root(repo_root) / "repo_context.json"


def resolve_battery_agents(agents: list[str] | None) -> list[str]:
    """Expand `all` and normalize agent ids to battery execution order."""
    if not agents:
        return list(BATTERY_ORDER)
    if any(str(a).lower() == "all" for a in agents):
        return list(BATTERY_ORDER)
    ordered: list[str] = []
    requested = {str(a).upper() for a in agents if str(a).upper() in BATTERY_AGENTS}
    for agent in BATTERY_ORDER:
        if agent in requested:
            ordered.append(agent)
    for agent in sorted(requested):
        if agent not in ordered:
            ordered.append(agent)
    return ordered or list(BATTERY_ORDER)


def ensure_eval_scaffold(repo_root: Path) -> None:
    root = artifacts_root(repo_root)
    (root / "runs").mkdir(parents=True, exist_ok=True)
    (repo_root / ".parallelops" / "dashboard").mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def start_session(
    repo_root: Path,
    *,
    task: str = "",
    mode: str = "build+verify",
    agents: list[str] | None = None,
    session_id: str | None = None,
) -> EvalSession:
    ensure_eval_scaffold(repo_root)
    sid = session_id or new_session_id()
    sel = load_json(selection_file(repo_root))
    resolved = resolve_battery_agents(list(agents or sel.get("agents") or list(BATTERY_ORDER)))
    repo_ctx = _repo_context(repo_root)
    session = EvalSession(
        session_id=sid,
        task=task or sel.get("task", "ParallelOps eval run"),
        mode=mode or sel.get("mode", "build+verify"),
        repo_root=repo_ctx["repo_root"],
        started_at=_now_iso(),
        agents=resolved,
    )
    save_json(repo_context_file(repo_root), {**repo_ctx, "updated_at": _now_iso()})
    save_json(session_file(repo_root), {"session_id": sid, **_session_to_dict(session)})
    save_json(run_dir(repo_root, sid) / "session.json", _session_to_dict(session))
    return session


def load_current_session(repo_root: Path) -> EvalSession | None:
    raw = load_json(session_file(repo_root))
    if not raw.get("session_id"):
        return None
    results = load_json(results_file(repo_root))
    agent_results = {}
    for agent, data in (results.get("agents") or {}).items():
        agent_results[agent] = AgentResult(agent=agent, **{k: v for k, v in data.items() if k != "agent"})
    return EvalSession(
        session_id=raw["session_id"],
        task=raw.get("task", ""),
        mode=raw.get("mode", "build+verify"),
        repo_root=raw.get("repo_root", str(repo_root)),
        started_at=raw.get("started_at", ""),
        finished_at=raw.get("finished_at"),
        agents=raw.get("agents", []),
        agent_results=agent_results,
    )


def _default_chart_plan(agent: str) -> dict[str, Any]:
    common = {
        "A1": [
            ("metrics", "execution_metrics", "Execution Metrics", "$.charts.execution_metrics"),
            ("timeline", "timeline", "Planning Timeline", "$.charts.timeline"),
            ("branches", "branch_graph", "Branch Graph", "$.charts.branch_graph"),
            ("worktrees", "worktree_graph", "Worktree Graph", "$.charts.worktree_graph"),
            ("success", "success_rate", "DoD Success Rate", "$.charts.success_rate"),
        ],
        "A2": [
            ("metrics", "execution_metrics", "Execution Metrics", "$.charts.execution_metrics"),
            ("timeline", "timeline", "Execution Timeline", "$.charts.timeline"),
            ("branches", "branch_graph", "Branch Graph", "$.charts.branch_graph"),
            ("worktrees", "worktree_graph", "Worktree Graph", "$.charts.worktree_graph"),
            ("success", "success_rate", "Merge Success Rate", "$.charts.success_rate"),
        ],
        "A3": [
            ("metrics", "execution_metrics", "Stack Metrics", "$.charts.execution_metrics"),
            ("timeline", "timeline", "Build Timeline", "$.charts.timeline"),
            ("flow", "branch_graph", "Pipeline Flow", "$.charts.branch_graph"),
            ("success", "success_rate", "Test Success Rate", "$.charts.success_rate"),
        ],
        "A4": [
            ("metrics", "execution_metrics", "Findings Metrics", "$.charts.execution_metrics"),
            ("severity", "severity_distribution", "Finding Severity", "$.charts.severity_distribution"),
            ("priority", "priority_matrix", "Priority Matrix", "$.charts.priority_matrix"),
            ("timeline", "timeline", "Timeline", "$.charts.timeline"),
            ("success", "success_rate", "Implementation Success", "$.charts.success_rate"),
        ],
        "A5": [
            ("metrics", "execution_metrics", "Review Metrics", "$.charts.execution_metrics"),
            ("severity", "severity_distribution", "Severity Distribution", "$.charts.severity_distribution"),
            ("timeline", "timeline", "Review Timeline", "$.charts.timeline"),
            ("success", "success_rate", "Verification Success", "$.charts.success_rate"),
        ],
    }
    sections = []
    for sid, component, title, binding in common.get(agent, common["A1"]):
        sections.append(
            {
                "id": sid,
                "component": component,
                "title": title,
                "bindings": {"data": binding},
            }
        )
    return {"schema_version": "1.0", "sections": sections}


def _default_report_md(agent: str, result: AgentResult, session: EvalSession) -> str:
    return f"""---
agent: {agent}
session_id: "{session.session_id}"
status: {result.status}
---

# {agent} — Eval Report

**Session:** `{session.session_id}`\
**Repository:** `{session.repo_root or "unknown"}`\
**Status:** {result.status}\
**Mode:** {result.mode}

## Summary

{result.summary or "No summary provided."}

## Artifacts

- `metadata.json` — run envelope
- `report.json` — structured data + charts
- `report.md` — this narrative
- `logs.txt` — command output
"""


def _build_metadata(result: AgentResult, session: EvalSession) -> dict[str, Any]:
    files = {name: name for name in ARTIFACT_FILES}
    repo_ctx = _repo_context(session.repo_root) if session.repo_root else {"repo_root": "", "repo_name": ""}
    return {
        "schema_version": "1.0",
        "agent": result.agent,
        "session_id": session.session_id,
        "status": result.status,
        "mode": result.mode,
        "repo_root": repo_ctx["repo_root"],
        "repo_name": repo_ctx["repo_name"],
        "started_at": result.started_at or session.started_at,
        "finished_at": result.finished_at or session.finished_at or _now_iso(),
        "duration_seconds": result.duration_seconds,
        "summary": result.summary,
        "files": files,
        "render_plan": {
            "schema_version": "1.0",
            "sections": [
                {
                    "id": "narrative",
                    "component": "markdown_file",
                    "title": "Report",
                    "bindings": {"path": "$.files.report_md"},
                    "source": "metadata",
                },
                {
                    "id": "logs",
                    "component": "log_viewer",
                    "title": "Logs",
                    "bindings": {"path": "$.files.logs_txt"},
                    "source": "metadata",
                },
            ],
        },
    }


def _build_report_json(result: AgentResult, session: EvalSession) -> dict[str, Any]:
    chart_plan = result.chart_plan or _default_chart_plan(result.agent)
    charts = result.charts or {
        "execution_metrics": [{"name": "Status", "value": 1 if result.status == "pass" else 0}],
        "timeline": [],
        "success_rate": {"current": 100 if result.status == "pass" else 0, "history": []},
    }
    return {
        "schema_version": "1.0",
        "agent": result.agent,
        "session_id": session.session_id,
        "status": result.status,
        "summary": result.summary,
        "repo_root": session.repo_root,
        "repo_name": _repo_context(session.repo_root)["repo_name"] if session.repo_root else "",
        "chart_plan": chart_plan,
        "charts": charts,
        "data": result.extra,
    }


def write_agent_bundle(
    repo_root: Path,
    session_id: str,
    result: AgentResult,
    session: EvalSession | None = None,
) -> dict[str, str]:
    """Write metadata.json, report.json, report.md, logs.txt for one agent."""
    session = session or EvalSession(
        session_id=session_id,
        started_at=_now_iso(),
        agents=[result.agent],
    )
    dest = agent_dir(repo_root, session_id, result.agent)
    dest.mkdir(parents=True, exist_ok=True)

    metadata = _build_metadata(result, session)
    report_json = _build_report_json(result, session)

    md_src = Path(result.report_md_path) if result.report_md_path else None
    if md_src and md_src.exists():
        shutil.copy2(md_src, dest / "report.md")
    else:
        (dest / "report.md").write_text(
            _default_report_md(result.agent, result, session), encoding="utf-8"
        )

    json_src = Path(result.report_json_path) if result.report_json_path else None
    if json_src and json_src.exists():
        existing = load_json(json_src)
        report_json = {**report_json, **existing, "session_id": session_id, "agent": result.agent}
    save_json(dest / "report.json", report_json)
    save_json(dest / "metadata.json", metadata)

    log_src = Path(result.logs_path) if result.logs_path else None
    if log_src and log_src.exists():
        shutil.copy2(log_src, dest / "logs.txt")
    else:
        (dest / "logs.txt").write_text(
            f"=== ParallelOps {result.agent} Log ===\nsession_id={session_id}\n"
            f"status={result.status}\n\n{result.summary}\n",
            encoding="utf-8",
        )

    return {k: str(dest / k) for k in ARTIFACT_FILES}


def _session_to_dict(session: EvalSession) -> dict[str, Any]:
    repo_ctx = _repo_context(session.repo_root) if session.repo_root else {"repo_root": "", "repo_name": ""}
    return {
        "session_id": session.session_id,
        "task": session.task,
        "mode": session.mode,
        "repo_root": repo_ctx["repo_root"] or session.repo_root,
        "repo_name": repo_ctx["repo_name"],
        "started_at": session.started_at,
        "finished_at": session.finished_at,
        "agents": session.agents,
        "agent_results": {k: asdict(v) for k, v in session.agent_results.items()},
    }


def record_agent_result(repo_root: Path, result: AgentResult, session_id: str | None = None) -> dict[str, str]:
    session = load_current_session(repo_root)
    sid = session_id or (session.session_id if session else None) or start_session(repo_root).session_id
    if session is None or session.session_id != sid:
        session = EvalSession(session_id=sid, started_at=_now_iso(), agents=[result.agent])

    session.repo_root = session.repo_root or str(repo_root.resolve())

    session.agent_results[result.agent] = result
    if result.agent not in session.agents:
        session.agents.append(result.agent)

    results = load_json(results_file(repo_root))
    agents_map = results.setdefault("agents", {})
    agents_map[result.agent] = asdict(result)
    results["session_id"] = sid
    save_json(results_file(repo_root), results)
    save_json(session_file(repo_root), _session_to_dict(session))

    paths = write_agent_bundle(repo_root, sid, result, session)
    return {"session_id": sid, **paths}


def _load_run_session(run_path: Path) -> dict[str, Any]:
    sf = run_path / "session.json"
    if sf.exists():
        return load_json(sf)
    meta = {"session_id": run_path.name, "agents": [], "agent_status": {}}
    scan_agents = BATTERY_AGENTS
    for agent in scan_agents:
        md = run_path / agent / "metadata.json"
        if md.exists():
            data = load_json(md)
            meta.setdefault("agents", []).append(agent)
            meta.setdefault("agent_status", {})[agent] = data.get("status", "unknown")
            meta.setdefault("summaries", {})[agent] = data.get("summary", "")
    return meta


def _aggregate_charts_from_run(run_path: Path, session_meta: dict[str, Any]) -> dict[str, Any]:
    charts: dict[str, Any] = {
        "execution_metrics": [],
        "timeline": [],
        "severity_distribution": [],
        "success_rate": {"current": 0, "history": []},
        "run_history": [],
    }
    agents = session_meta.get("agents", [])
    pass_count = 0
    for agent in agents:
        rp = run_path / agent / "report.json"
        if not rp.exists():
            continue
        data = load_json(rp)
        status = data.get("status", "unknown")
        if status == "pass":
            pass_count += 1
        charts["execution_metrics"].append(
            {"name": agent, "value": 1 if status == "pass" else 0 if status == "fail" else 0.5}
        )
        for event in (data.get("charts") or {}).get("timeline") or []:
            charts["timeline"].append({**event, "phase": event.get("phase", agent)})
        for slice_ in (data.get("charts") or {}).get("severity_distribution") or []:
            charts["severity_distribution"].append(slice_)
    total = len(agents) or 1
    charts["success_rate"] = {
        "current": round(100 * pass_count / total, 1),
        "label": f"Session {session_meta.get('session_id', '')}",
        "history": [{"label": a, "rate": 100} for a in agents],
    }
    return charts


def _agents_on_disk(run_path: Path, declared: list[str] | None = None) -> list[str]:
    """Agents that actually have a bundle under runs/{session}/{agent}/."""
    candidates = declared or list(BATTERY_AGENTS)
    found = [a for a in candidates if (run_path / a / "metadata.json").exists()]
    if found:
        return found
    return [a for a in BATTERY_AGENTS if (run_path / a / "metadata.json").exists()]


def build_index(repo_root: Path, *, selected_session_id: str | None = None) -> Path:
    """Rebuild index.json from all runs/*/session.json (execution history)."""
    ensure_eval_scaffold(repo_root)
    runs = runs_root(repo_root)
    sessions: list[dict[str, Any]] = []

    if runs.exists():
        for run_path in sorted(runs.iterdir(), reverse=True):
            if not run_path.is_dir():
                continue
            meta = _load_run_session(run_path)
            sid = meta.get("session_id", run_path.name)
            agents = _agents_on_disk(run_path, meta.get("agents"))
            statuses = meta.get("agent_status") or {}
            if not statuses:
                for a in agents:
                    md = run_path / a / "metadata.json"
                    if md.exists():
                        statuses[a] = load_json(md).get("status", "unknown")
            overall = "pass"
            if any(s == "fail" for s in statuses.values()):
                overall = "fail"
            elif any(s in ("partial", "running") for s in statuses.values()):
                overall = "partial"
            sessions.append(
                {
                    "session_id": sid,
                    "task": meta.get("task", "ParallelOps eval"),
                    "mode": meta.get("mode", "build+verify"),
                    "repo_root": meta.get("repo_root", ""),
                    "repo_name": meta.get("repo_name")
                    or (_repo_context(meta["repo_root"])["repo_name"] if meta.get("repo_root") else ""),
                    "started_at": meta.get("started_at", ""),
                    "finished_at": meta.get("finished_at"),
                    "agents": agents,
                    "overall_status": overall,
                    "agent_status": statuses,
                }
            )

    selected = selected_session_id or (sessions[0]["session_id"] if sessions else "")
    selected_meta = next((s for s in sessions if s["session_id"] == selected), sessions[0] if sessions else {})

    run_path = runs / selected if selected else None
    charts = _aggregate_charts_from_run(run_path, selected_meta) if run_path and run_path.exists() else {}

    if sessions:
        charts["run_history"] = [
            {
                "name": s["session_id"][-6:],
                "value": max(1, len(s.get("agents", [])) * 10),
            }
            for s in sessions[:5]
        ]

    index = {
        "schema_version": "1.0",
        "updated_at": _now_iso(),
        "selected_session_id": selected,
        "execution_status": selected_meta.get("overall_status", "pass") if selected_meta else "pass",
        "repo_root": selected_meta.get("repo_root", "") if selected_meta else "",
        "repo_name": selected_meta.get("repo_name", "") if selected_meta else "",
        "sessions": sessions,
        "agents": list(BATTERY_AGENTS),
        "selected_evaluation": {
            "session_id": selected,
            "task": selected_meta.get("task", ""),
            "mode": selected_meta.get("mode", "build+verify"),
            "repo_root": selected_meta.get("repo_root", ""),
            "repo_name": selected_meta.get("repo_name", ""),
            "overall_status": selected_meta.get("overall_status", "pass"),
            "agents": selected_meta.get("agents", []),
        },
        "chart_plan": {
            "schema_version": "1.0",
            "sections": [
                {
                    "id": "metrics",
                    "component": "execution_metrics",
                    "title": "Execution Metrics",
                    "bindings": {"data": "$.charts.execution_metrics"},
                },
                {
                    "id": "timeline",
                    "component": "timeline",
                    "title": "Session Timeline",
                    "bindings": {"data": "$.charts.timeline"},
                },
                {
                    "id": "severity",
                    "component": "severity_distribution",
                    "title": "Agent Status Distribution",
                    "bindings": {"data": "$.charts.severity_distribution"},
                },
                {
                    "id": "agent_success",
                    "component": "success_rate",
                    "title": "Session Success Rate",
                    "bindings": {"data": "$.charts.success_rate"},
                },
                {
                    "id": "run_history",
                    "component": "execution_metrics",
                    "title": "Recent Runs",
                    "bindings": {"data": "$.charts.run_history"},
                },
            ],
        },
        "charts": charts,
    }
    return save_json(index_file(repo_root), index)


def _legacy_session_id(repo_root: Path) -> str:
    idx = load_json(index_file(repo_root))
    sel = idx.get("selected_evaluation") or {}
    return str(sel.get("session_id") or "20260617-074928")


def _ensure_missing_bundle_files(
    agent_dest: Path,
    agent: str,
    session_id: str,
    *,
    task: str = "ParallelOps eval",
    mode: str = "build+verify",
) -> None:
    """Fill metadata.json / logs.txt when only report.md+json exist (legacy layout)."""
    report_json_path = agent_dest / "report.json"
    report_md_path = agent_dest / "report.md"
    report_data = load_json(report_json_path) if report_json_path.exists() else {}
    status = str(report_data.get("status", "pass"))
    summary = str(report_data.get("summary", ""))

    session = EvalSession(
        session_id=session_id,
        task=task,
        mode=mode,
        started_at="2026-06-17T07:49:28Z",
        finished_at="2026-06-17T08:42:11Z",
        agents=[agent],
    )
    result = AgentResult(
        agent=agent,
        status=status,
        mode=mode,
        summary=summary,
        charts=report_data.get("charts") or {},
        chart_plan=report_data.get("chart_plan"),
    )

    if not report_md_path.exists():
        (agent_dest / "report.md").write_text(
            _default_report_md(agent, result, session), encoding="utf-8"
        )
    if not report_json_path.exists():
        save_json(report_json_path, _build_report_json(result, session))
    if not (agent_dest / "metadata.json").exists():
        save_json(agent_dest / "metadata.json", _build_metadata(result, session))
    if not (agent_dest / "logs.txt").exists():
        (agent_dest / "logs.txt").write_text(
            f"=== ParallelOps {agent} Log ===\n"
            f"session_id={session_id}\nstatus={status}\n\n{summary or 'No logs captured.'}\n",
            encoding="utf-8",
        )


def migrate_legacy_flat_artifacts(
    repo_root: Path,
    session_id: str | None = None,
) -> str | None:
    """Copy legacy artifacts/A{n}/ files into runs/{session_id}/A{n}/."""
    art = artifacts_root(repo_root)
    sid = session_id or _legacy_session_id(repo_root)
    dest_run = run_dir(repo_root, sid)
    dest_run.mkdir(parents=True, exist_ok=True)

    idx = load_json(index_file(repo_root))
    sel = idx.get("selected_evaluation") or {}
    task = str(sel.get("task") or "Migrated legacy eval artifacts")
    mode = str(sel.get("mode") or "build+verify")

    agents_found: list[str] = []
    agent_status: dict[str, str] = {}
    for agent in BATTERY_AGENTS:
        src = art / agent
        if not src.exists():
            continue
        agents_found.append(agent)
        agent_dest = dest_run / agent
        agent_dest.mkdir(parents=True, exist_ok=True)
        for name in ARTIFACT_FILES:
            f = src / name
            if f.exists():
                shutil.copy2(f, agent_dest / name)
        _ensure_missing_bundle_files(agent_dest, agent, sid, task=task, mode=mode)
        md = load_json(agent_dest / "metadata.json")
        agent_status[agent] = md.get("status", "pass")

    if agents_found:
        repo_ctx = _repo_context(repo_root)
        save_json(
            dest_run / "session.json",
            {
                "session_id": sid,
                "task": task,
                "mode": mode,
                "repo_root": repo_ctx["repo_root"],
                "repo_name": repo_ctx["repo_name"],
                "started_at": str(sel.get("started_at") or "2026-06-17T07:49:28Z"),
                "finished_at": str(sel.get("finished_at") or "2026-06-17T08:42:11Z"),
                "agents": agents_found,
                "agent_status": agent_status,
                "overall_status": str(sel.get("overall_status") or "pass"),
            },
        )
        return sid
    return None


def finalize_eval(repo_root: Path, session_id: str | None = None) -> dict[str, Any]:
    """Finalize session: write all agent bundles from eval_results, rebuild index."""
    ensure_eval_scaffold(repo_root)
    migrated = migrate_legacy_flat_artifacts(repo_root, session_id=session_id)

    session = load_current_session(repo_root)
    sid = session_id or (session.session_id if session else None) or migrated
    if not sid:
        sid = start_session(repo_root).session_id

    results = load_json(results_file(repo_root))
    if session is None:
        session = EvalSession(session_id=sid, started_at=_now_iso())

    for agent, data in (results.get("agents") or {}).items():
        result = AgentResult(agent=agent, **{k: v for k, v in data.items() if k != "agent"})
        write_agent_bundle(repo_root, sid, result, session)

    for agent in BATTERY_AGENTS:
        legacy = artifacts_root(repo_root) / agent
        run_agent = agent_dir(repo_root, sid, agent)
        if legacy.exists() and not (run_agent / "report.md").exists():
            run_agent.mkdir(parents=True, exist_ok=True)
            for name in ARTIFACT_FILES:
                f = legacy / name
                if f.exists():
                    shutil.copy2(f, run_agent / name)
            _ensure_missing_bundle_files(
                run_agent,
                agent,
                sid,
                task=session.task or "ParallelOps eval",
                mode=session.mode,
            )

    run_session_path = run_dir(repo_root, sid) / "session.json"
    existing_run = load_json(run_session_path)
    repo_ctx = _repo_context(repo_root)
    if existing_run.get("agents"):
        existing_run["finished_at"] = _now_iso()
        existing_run["agents"] = _agents_on_disk(run_dir(repo_root, sid), existing_run.get("agents"))
        if not existing_run.get("repo_root"):
            existing_run["repo_root"] = repo_ctx["repo_root"]
            existing_run["repo_name"] = repo_ctx["repo_name"]
        save_json(run_session_path, existing_run)
    else:
        session.finished_at = _now_iso()
        session.repo_root = session.repo_root or repo_ctx["repo_root"]
        session.agents = _agents_on_disk(run_dir(repo_root, sid), session.agents or None)
        if not session.agents:
            session.agents = _agents_on_disk(run_dir(repo_root, sid), None)
        save_json(run_session_path, _session_to_dict(session))

    save_json(repo_context_file(repo_root), {**repo_ctx, "updated_at": _now_iso()})
    index_path = build_index(repo_root, selected_session_id=sid)
    dashboard_url = f"http://localhost:3000/?session={sid}"
    return {
        "session_id": sid,
        "index_path": str(index_path),
        "dashboard_url": dashboard_url,
        "runs_dir": str(run_dir(repo_root, sid)),
    }


def find_agent_report_md(repo_root: Path, agent: str) -> Path | None:
    """Locate the best markdown report for an agent (artifact or task folder)."""
    for rel in AGENT_MD_SOURCES.get(agent, ()):
        path = repo_root / rel
        if path.is_file() and path.stat().st_size > 0:
            return path
    legacy = artifacts_root(repo_root) / agent / "report.md"
    if legacy.is_file() and legacy.stat().st_size > 0:
        return legacy
    return None


def build_dashboard_from_markdown(
    repo_root: Path,
    *,
    agents: list[str] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Build dashboard session from existing markdown only — no subagent execution.
    Scans A1–A6 report paths, writes artifact bundles, rebuilds index.json.
    """
    ensure_eval_scaffold(repo_root)
    target_agents = list(agents or BATTERY_AGENTS)
    session = start_session(
        repo_root,
        task="Dashboard from existing MD reports (A1–A6)",
        mode="dashboard",
        agents=target_agents,
        session_id=session_id,
    )
    sid = session.session_id
    recorded: list[str] = []
    missing: list[str] = []

    for agent in target_agents:
        md_path = find_agent_report_md(repo_root, agent)
        if md_path is None:
            missing.append(agent)
            continue
        try:
            rel = md_path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            rel = md_path.name
        record_agent_result(
            repo_root,
            AgentResult(
                agent=agent,
                status="pass",
                mode="dashboard",
                summary=f"Report ingested from {rel}",
                report_md_path=str(md_path.resolve()),
            ),
            session_id=sid,
        )
        recorded.append(agent)

    session.agents = recorded
    save_json(session_file(repo_root), {"session_id": sid, **_session_to_dict(session)})
    run_meta = _session_to_dict(session)
    run_meta["finished_at"] = _now_iso()
    save_json(run_dir(repo_root, sid) / "session.json", run_meta)

    out = finish_eval_and_dashboard(
        repo_root,
        session_id=sid,
        agents=recorded or None,
        start_server=False,
    )
    out["agents_from_md"] = recorded
    out["agents_missing_md"] = missing
    return out


def sync_session_agents_from_reports(
    repo_root: Path,
    session_id: str,
    agents: list[str],
    *,
    mode: str = "build+verify",
) -> tuple[list[str], list[str]]:
    """Ensure each agent in the session has a four-file bundle (from MD if needed)."""
    session = load_current_session(repo_root)
    if session is None:
        session = EvalSession(session_id=session_id, started_at=_now_iso(), agents=agents, mode=mode)
    results = load_json(results_file(repo_root))
    recorded: list[str] = []
    missing: list[str] = []

    for agent in agents:
        bundle = agent_dir(repo_root, session_id, agent)
        if (bundle / "report.md").exists() and (bundle / "metadata.json").exists():
            recorded.append(agent)
            continue

        prior = (results.get("agents") or {}).get(agent, {})
        md_path = find_agent_report_md(repo_root, agent)
        report_md = prior.get("report_md_path")
        if report_md and Path(report_md).exists():
            md_path = Path(report_md)
        elif md_path is None:
            missing.append(agent)
            continue

        try:
            rel = md_path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            rel = md_path.name

        record_agent_result(
            repo_root,
            AgentResult(
                agent=agent,
                status=str(prior.get("status", "pass")),
                mode=str(prior.get("mode", mode)),
                summary=str(prior.get("summary") or f"Report ingested from {rel}"),
                report_md_path=str(md_path.resolve()),
                report_json_path=prior.get("report_json_path"),
                logs_path=prior.get("logs_path"),
            ),
            session_id=session_id,
        )
        recorded.append(agent)

    return recorded, missing


def write_dashboard_manifest(
    repo_root: Path,
    *,
    session_id: str,
    dashboard_url: str,
    agents_synced: list[str],
    agents_missing: list[str],
) -> Path:
    repo_ctx = _repo_context(repo_root)
    manifest = {
        "schema_version": "1.0",
        "session_id": session_id,
        "dashboard_url": dashboard_url,
        "repo_root": repo_ctx["repo_root"],
        "repo_name": repo_ctx["repo_name"],
        "updated_at": _now_iso(),
        "agents_synced": agents_synced,
        "agents_missing": agents_missing,
    }
    save_json(dashboard_manifest_file(repo_root), manifest)
    dashboard_url_file(repo_root).write_text(dashboard_url + "\n", encoding="utf-8")
    return dashboard_manifest_file(repo_root)


def finish_eval_and_dashboard(
    repo_root: Path,
    *,
    session_id: str | None = None,
    agents: list[str] | None = None,
    port: int = 3000,
    start_server: bool = True,
    foreground: bool = False,
) -> dict[str, Any]:
    """
    Post-battery hook: sync A1–A6 artifacts, rebuild index, write URL, start dashboard.
    Call this after all agents finish (or after eval-record for each agent).
    """
    ensure_eval_scaffold(repo_root)
    session = load_current_session(repo_root)
    sel = load_json(selection_file(repo_root))
    sid = session_id or (session.session_id if session else None)
    if not sid:
        started = start_session(repo_root, agents=resolve_battery_agents(agents))
        sid = started.session_id
        session = started

    target_agents = resolve_battery_agents(
        agents or (session.agents if session else None) or sel.get("agents")
    )
    mode = str(sel.get("mode") or (session.mode if session else "build+verify"))

    synced, missing = sync_session_agents_from_reports(
        repo_root, sid, target_agents, mode=mode
    )
    out = finalize_eval(repo_root, session_id=sid)
    out["agents_synced"] = synced
    out["agents_missing"] = missing

    from parallelops.dashboard_server import ensure_dashboard_running, resolve_dashboard_port

    resolved_port = resolve_dashboard_port(repo_root, preferred=port)
    if start_server:
        dash = ensure_dashboard_running(
            repo_root,
            port=resolved_port,
            session_id=sid,
            foreground=foreground,
        )
        out.update(dash)
        resolved_port = int(dash.get("port", resolved_port))

    url = f"http://localhost:{resolved_port}/?session={sid}"
    out["dashboard_url"] = url
    write_dashboard_manifest(
        repo_root,
        session_id=sid,
        dashboard_url=url,
        agents_synced=synced,
        agents_missing=missing,
    )

    return out
