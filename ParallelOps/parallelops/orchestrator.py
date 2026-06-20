"""Orchestrator: discovery → analysis → A1 → approval → A2 → report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from parallelops.a1_planner import A1PlannerAgent
from parallelops.a2_executor import A2ExecutorAgent
from parallelops.approval import is_approved, is_merge_approved, save_approval, save_merge_approval
from parallelops.models import ExecutionPolicy
from parallelops.plan_preview import write_plan_preview


@dataclass
class UserRequest:
    """Phase 1 discovery answers — saved to user_request.json."""

    # Repository (Q1–Q2)
    repo_path: str = "."
    base_branch: str = "main"

    # Task (Q3–Q4)
    task_description: str = ""
    max_parallel_lanes: int = 3

    # Execution policy (Q5–Q8)
    auto_generate_tasks: bool = True
    auto_commit_lanes: bool = False
    auto_push_lanes: bool = False
    require_merge_approval: bool = True

    # Branch / worktree (sensible defaults for any repo)
    branch_naming_convention: str = "{prefix}/{task_slug}"
    worktree_base_dir: str = ".parallelops/worktrees"
    artifact_location: str = ".parallelops/artifacts"

    # Legacy compat (derived from new fields)
    can_parallelize: bool = True
    single_or_multi: str = "multi"
    mode: str = "interactive"
    auto_merge: bool = True
    pause_on_conflict: bool = True
    push_final_branch: bool = False
    require_manual_approval: bool = True

    # Verification (Q9)
    verification_commands: list[str] = field(default_factory=list)

    # Pipeline control
    run_a2: bool = False
    approved: bool = False
    dry_run: bool = False


def ensure_scaffold(repo_root: Path) -> None:
    dirs = [
        ".parallelops/artifacts",
        ".parallelops/artifacts/lane_prompts",
        ".parallelops/artifacts/runs",
        ".parallelops/sessions",
        ".parallelops/reports",
        ".parallelops/logs",
        ".parallelops/worktrees",
        ".parallelops/dashboard",
    ]
    for d in dirs:
        p = repo_root / d
        p.mkdir(parents=True, exist_ok=True)


def _policy_from_request(request: UserRequest) -> ExecutionPolicy:
    auto_commit = request.auto_commit_lanes
    mode = "automatic" if auto_commit else "interactive"
    request.mode = mode
    request.can_parallelize = request.max_parallel_lanes > 1
    request.single_or_multi = "multi" if request.max_parallel_lanes > 1 else "single"
    request.auto_merge = True
    request.push_final_branch = request.auto_push_lanes
    request.require_manual_approval = True  # always gate A2 via plan approval

    return ExecutionPolicy(
        base_branch=request.base_branch,
        auto_generate_tasks=request.auto_generate_tasks,
        auto_commit_lanes=auto_commit,
        auto_push_lanes=request.auto_push_lanes,
        auto_merge=request.auto_merge,
        pause_on_conflict=request.pause_on_conflict,
        push_final_branch=request.push_final_branch,
        require_manual_approval=request.require_manual_approval,
        require_merge_approval=request.require_merge_approval,
        verification_commands=list(request.verification_commands),
    )


def run_a1(repo_root: Path, request: UserRequest) -> dict:
    """Phase 2–3: analyze repo and invoke A1 only."""
    if request.repo_path in (".", ""):
        target = repo_root.resolve()
    else:
        target = Path(request.repo_path).resolve()
    ensure_scaffold(target)

    policy = _policy_from_request(request)
    scope = "single" if request.max_parallel_lanes <= 1 else "multi"

    planner = A1PlannerAgent(target)
    plan = planner.plan(
        request.task_description,
        mode=request.mode,
        single_or_multi=scope,
        can_parallelize=request.max_parallel_lanes > 1,
        max_parallel_lanes=request.max_parallel_lanes,
        auto_generate_tasks=request.auto_generate_tasks,
        worktree_base_dir=request.worktree_base_dir,
        branch_naming_convention=request.branch_naming_convention,
        artifact_location=request.artifact_location,
        execution_policy=policy,
    )
    artifact_path = planner.save_artifact(plan)
    preview_path = write_plan_preview(plan, target)

    save_user_request_json(request, target / request.artifact_location / "user_request.json")

    return {
        "phase": "a1_complete",
        "session_id": plan.session_id,
        "artifact_path": str(artifact_path),
        "plan_preview_path": str(preview_path),
        "lanes": [lane.name for lane in plan.parallel_lanes],
        "branch_names": plan.branch_names,
        "worktree_names": plan.worktree_names,
        "merge_order": plan.merge_order,
        "repository_analysis": plan.repository_analysis,
        "awaiting_approval": True,
    }


def run_a2(repo_root: Path, *, dry_run: bool = False, skip_implementation: bool = False) -> dict:
    """Phase 4: invoke A2 from existing artifact."""
    from parallelops.report_builder import build_final_report

    repo_root = repo_root.resolve()
    executor = A2ExecutorAgent(repo_root)
    plan = executor.load_plan()
    if plan.execution_policy.require_manual_approval and not is_approved(
        repo_root, plan.session_id, plan.preferences.artifact_location
    ):
        raise RuntimeError(
            "Execution not approved. Review .parallelops/reports/plan_preview.md "
            "then run: python -m parallelops.cli approve"
        )
    session = executor.execute(plan, dry_run=dry_run, skip_lane_implementation=skip_implementation)
    report_path = build_final_report(session, repo_root)
    return {
        "phase": "a2_complete",
        "session_id": plan.session_id,
        "session_dir": str(session.session_dir),
        "report_path": str(report_path),
        "paused_for_conflict": session.paused_for_conflict,
        "lane_statuses": {ls.lane.id: ls.status.value for ls in session.lanes},
        "final_status": session.final_status,
    }


def run_pipeline(repo_root: Path, request: UserRequest) -> dict:
    """Full pipeline with optional approval gate."""
    result = run_a1(repo_root, request)
    if not request.run_a2:
        return result
    if request.approved:
        save_approval(
            Path(request.repo_path or repo_root).resolve(),
            result["session_id"],
            request.artifact_location,
        )
        result.update(run_a2(Path(request.repo_path or repo_root), dry_run=request.dry_run))
    else:
        result["phase"] = "awaiting_approval"
    return result


def load_user_request_json(path: Path) -> UserRequest:
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {f.name for f in fields(UserRequest)}
    return UserRequest(**{k: v for k, v in data.items() if k in names})


def save_user_request_json(request: UserRequest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(request), indent=2), encoding="utf-8")


def discovery_template() -> dict:
    return asdict(
        UserRequest(
            task_description="DESCRIBE_CHANGES_HERE",
            max_parallel_lanes=3,
            auto_generate_tasks=True,
            auto_push_lanes=True,
            verification_commands=["npm run lint", "npm run build", "npm test"],
        )
    )
