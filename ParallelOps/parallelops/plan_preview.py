"""Phase 4 — human-readable plan preview for approval gate."""

from __future__ import annotations

from pathlib import Path

from parallelops.models import ExecutionPlan


def build_plan_preview(plan: ExecutionPlan) -> str:
    lines = [
        "# ParallelOps Execution Plan (A1)",
        "",
        f"**Session:** `{plan.session_id}`",
        f"**Task:** {plan.task.description}",
        f"**Repo:** `{plan.task.repo_root}`",
        f"**Base branch:** `{plan.execution_policy.base_branch}`",
        f"**Mode:** {plan.task.mode}",
        "",
        "## Task decomposition",
    ]
    for lane in plan.parallel_lanes:
        lines.append(f"### {lane.id} — {lane.name}")
        lines.append(f"- **Goal:** {lane.goal}")
        lines.append(f"- **Branch:** `{lane.branch_name}`")
        lines.append(f"- **Worktree:** `{lane.worktree_name}` → `{lane.worktree_path}`")
        lines.append(f"- **Owns:** {', '.join(f'`{p}`' for p in lane.files_owned) or '_(see prompt)_'}")
        lines.append("")

    lines.extend(["## Branch names"] + [f"- `{b}`" for b in plan.branch_names])
    lines.extend(["", "## Worktree names"] + [f"- `{w}`" for w in plan.worktree_names])

    lines.extend(["", "## Merge order"])
    for i, lane_id in enumerate(plan.merge_order, 1):
        lane = next((l for l in plan.parallel_lanes if l.id == lane_id), None)
        name = lane.name if lane else lane_id
        lines.append(f"{i}. **{lane_id}** ({name})")

    lines.extend(["", "## Risk analysis"])
    for risk in plan.risk_plan:
        lines.append(f"- **[{risk.category}]** {risk.description}")
        lines.append(f"  - Mitigation: {risk.mitigation}")

    lines.extend(["", "## Verification plan"])
    for step in plan.verification_plan:
        req = "required" if step.required else "optional"
        lines.append(f"- **{step.name}** ({req}): `{step.command}`")

    lines.extend(
        [
            "",
            "## Execution policy",
            f"- Auto-commit lanes: `{plan.execution_policy.auto_commit_lanes}`",
            f"- Auto-push lanes: `{plan.execution_policy.auto_push_lanes}`",
            f"- Auto-merge: `{plan.execution_policy.auto_merge}`",
            f"- Pause on conflict: `{plan.execution_policy.pause_on_conflict}`",
            f"- Push final branch: `{plan.execution_policy.push_final_branch}`",
            f"- Require merge approval: `{plan.execution_policy.require_merge_approval}`",
            "",
            "---",
            "",
            "**Approve execution?** Reply `yes` to run A2, or edit `.parallelops/artifacts/a1_execution_plan.yaml` first.",
            "",
        ]
    )
    return "\n".join(lines)


def write_plan_preview(plan: ExecutionPlan, repo_root: Path) -> Path:
    path = repo_root / ".parallelops/reports/plan_preview.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_plan_preview(plan), encoding="utf-8")
    return path
