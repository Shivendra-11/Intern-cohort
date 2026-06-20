"""Run coding agents in parallel worktree lanes."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from parallelops import git_ops
from parallelops.models import ExecutionPlan, ParallelLane


@dataclass
class LaneRunResult:
    lane_id: str
    lane_name: str
    worktree_path: str
    branch_name: str
    status: str  # done | skipped | error | no_sdk
    agent_output: str = ""
    commits: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    pushed: bool = False
    push_log: str = ""
    github_url: str | None = None
    error: str = ""


def _resolve_worktree(repo_root: Path, configured: str) -> Path:
    p = Path(configured)
    if not p.is_absolute():
        p = repo_root / p
    return p.resolve()


def _lane_prompt_path(repo_root: Path, plan: ExecutionPlan, lane_id: str) -> Path:
    return repo_root / plan.preferences.artifact_location / "lane_prompts" / f"{lane_id}.prompt.md"


def _commit_message(lane: ParallelLane) -> str:
    for d in lane.deliverables:
        if d.startswith("Commit: `"):
            return d.replace("Commit: `", "").rstrip("`")
    return f"feat({lane.worktree_name}): lane implementation"


def build_lane_coding_prompt(repo_root: Path, plan: ExecutionPlan, lane: ParallelLane) -> str:
    """Full prompt sent to each lane coding agent."""
    prompt_path = _lane_prompt_path(repo_root, plan, lane.id)
    base = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    wt = _resolve_worktree(repo_root, lane.worktree_path)
    commit_msg = _commit_message(lane)

    return f"""You are a lane coding agent for ParallelOps worktree `{lane.worktree_name}`.

## Rules
- Work ONLY inside this directory: `{wt}`
- Make REAL code changes (not placeholders) for the lane goal
- Only modify files in files_owned; never touch files_forbidden
- Run relevant tests for your lane if applicable
- When done: `git add -A && git commit -m "{commit_msg}"` (skip commit if nothing changed)
- End your reply with: STATUS: DONE and a bullet list of changed file paths

## Lane specification
{base}
"""


def _ensure_commit(wt_path: Path, message: str) -> list[str]:
    status = git_ops.run_git(wt_path, "status", "--porcelain")
    if not status.stdout.strip():
        return []
    git_ops.run_git(wt_path, "add", "-A")
    git_ops.run_git(wt_path, "commit", "-m", message)
    log = git_ops.run_git(wt_path, "log", "--oneline", "-3")
    return [l.strip() for l in log.stdout.splitlines() if l.strip()]


def _run_lane_sdk(
    repo_root: Path,
    plan: ExecutionPlan,
    lane: ParallelLane,
    *,
    api_key: str,
    model: str,
) -> LaneRunResult:
    wt_path = _resolve_worktree(repo_root, lane.worktree_path)
    result = LaneRunResult(
        lane_id=lane.id,
        lane_name=lane.name,
        worktree_path=str(wt_path),
        branch_name=lane.branch_name,
        status="error",
    )
    if not wt_path.exists():
        result.error = f"worktree missing: {wt_path} — run approve --execute --setup-only first"
        return result

    prompt = build_lane_coding_prompt(repo_root, plan, lane)
    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions

        agent_result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=str(wt_path)),
            ),
        )
        result.agent_output = (agent_result.result or "")[:8000]
        result.status = "done" if agent_result.status != "error" else "error"
        if agent_result.status == "error":
            result.error = result.agent_output[:500]
    except ImportError:
        result.status = "no_sdk"
        result.error = "cursor-sdk not installed — pip install cursor-sdk"
        return result
    except Exception as exc:  # noqa: BLE001
        result.status = "error"
        result.error = str(exc)
        return result

    commit_msg = _commit_message(lane)
    result.commits = _ensure_commit(wt_path, commit_msg)
    result.changed_files = git_ops.get_changed_files(
        repo_root, lane.branch_name, base=plan.execution_policy.base_branch
    )

    if plan.execution_policy.auto_push_lanes:
        push = git_ops.push_branch(repo_root, lane.branch_name)
        result.pushed = push.ok
        result.push_log = push.output
        result.github_url = push.github_url

    return result


def run_lanes_with_sdk(
    repo_root: Path,
    plan: ExecutionPlan,
    *,
    api_key: str | None = None,
    model: str = "composer-2.5",
    max_workers: int | None = None,
) -> list[LaneRunResult]:
    """Run all lanes in parallel via Cursor SDK (requires CURSOR_API_KEY)."""
    key = api_key or os.environ.get("CURSOR_API_KEY")
    if not key:
        raise RuntimeError(
            "CURSOR_API_KEY not set. Export it or use Cursor chat lane dispatch (see SKILL.md)."
        )

    workers = max_workers or len(plan.parallel_lanes)
    results: list[LaneRunResult] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_run_lane_sdk, repo_root, plan, lane, api_key=key, model=model): lane
            for lane in plan.parallel_lanes
        }
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: r.lane_id)
    _write_lane_results(repo_root, plan, results)
    return results


def write_lane_dispatch_manifest(repo_root: Path, plan: ExecutionPlan) -> Path:
    """JSON manifest for Cursor chat to launch parallel Task agents."""
    session_dir = repo_root / ".parallelops/sessions" / plan.session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    lanes = []
    for lane in plan.parallel_lanes:
        wt = _resolve_worktree(repo_root, lane.worktree_path)
        lanes.append(
            {
                "lane_id": lane.id,
                "name": lane.name,
                "branch": lane.branch_name,
                "worktree_path": str(wt),
                "prompt_file": str(_lane_prompt_path(repo_root, plan, lane.id)),
                "commit_message": _commit_message(lane),
                "coding_prompt": build_lane_coding_prompt(repo_root, plan, lane),
            }
        )

    manifest = {
        "session_id": plan.session_id,
        "repo_root": str(repo_root.resolve()),
        "dispatch": "Launch one Task subagent per lane IN PARALLEL using coding_prompt",
        "lanes": lanes,
    }
    path = session_dir / "lane_dispatch.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _write_lane_results(repo_root: Path, plan: ExecutionPlan, results: list[LaneRunResult]) -> Path:
    session_dir = repo_root / ".parallelops/sessions" / plan.session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "lane_results.json"
    payload = {
        "session_id": plan.session_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "results": [asdict(r) for r in results],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def implement_lanes(
    repo_root: Path,
    *,
    use_sdk: bool = True,
    model: str = "composer-2.5",
) -> dict:
    """Implement all lanes — SDK if available, else write dispatch manifest."""
    repo_root = repo_root.resolve()
    artifact = repo_root / ".parallelops/artifacts/a1_execution_plan.yaml"
    if not artifact.exists():
        raise FileNotFoundError(f"No A1 plan at {artifact}. Run plan first.")

    plan = ExecutionPlan.load(artifact)
    manifest_path = write_lane_dispatch_manifest(repo_root, plan)

    if use_sdk and os.environ.get("CURSOR_API_KEY"):
        try:
            results = run_lanes_with_sdk(repo_root, plan, model=model)
            from parallelops.a2_executor import PushRecord
            from parallelops.github_push import write_github_push_report

            push_records = [
                PushRecord(r.branch_name, r.pushed, r.push_log, r.github_url) for r in results
            ]
            gh_path = write_github_push_report(repo_root, plan, push_records)
            return {
                "mode": "cursor_sdk",
                "manifest_path": str(manifest_path),
                "github_push_summary": str(gh_path),
                "lanes": [asdict(r) for r in results],
                "all_done": all(r.status == "done" for r in results),
            }
        except ImportError:
            pass

    return {
        "mode": "cursor_chat_dispatch",
        "manifest_path": str(manifest_path),
        "message": (
            "Set CURSOR_API_KEY + pip install cursor-sdk for automatic lane coding, "
            "OR open lane_dispatch.json and launch parallel Task agents in Cursor chat."
        ),
        "lanes": len(plan.parallel_lanes),
    }
