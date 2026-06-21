"""Build final_summary.md from an A2 execution session."""

from __future__ import annotations

from pathlib import Path

from parallelops import git_ops
from parallelops.a2_executor import ExecutionSession, LaneStatus
from parallelops.github_push import write_github_push_report


def build_final_report(session: ExecutionSession, repo_root: Path) -> Path:
    plan = session.plan
    policy = plan.execution_policy
    reports_dir = repo_root / ".parallelops/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "final_summary.md"

    lines = [
        "# ParallelOps Final Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Session | `{plan.session_id}` |",
        f"| Task | {plan.task.description} |",
        f"| Repo | `{plan.task.repo_root}` |",
        f"| Base branch | `{policy.base_branch}` |",
        f"| Mode | {plan.task.mode} |",
        f"| Status | **{session.final_status}** |",
        "",
        "## Lanes",
    ]
    for ls in session.lanes:
        icon = {
            LaneStatus.COMPLETED: "✅",
            LaneStatus.FAILED: "❌",
            LaneStatus.RUNNING: "🔄",
            LaneStatus.CANCELLED: "⛔",
            LaneStatus.PENDING: "⏳",
        }.get(ls.status, "?")
        lines.append(f"### {icon} {ls.lane.id} — {ls.lane.name}")
        lines.append(f"- Branch: `{ls.lane.branch_name}`")
        lines.append(f"- Worktree: `{ls.lane.worktree_name}`")
        if ls.commits:
            lines.append("- Commits:")
            for c in ls.commits:
                lines.append(f"  - `{c}`")
        if ls.changed_files:
            lines.append("- Changed files:")
            for f in ls.changed_files[:15]:
                lines.append(f"  - `{f}`")
        if ls.pushed:
            lines.append("- Push: ✅ lane on GitHub")
            if ls.push_log:
                lines.append(f"  - `{ls.push_log[:120]}`")
        elif policy.auto_push_lanes:
            lines.append("- Push: ⚠️ failed or skipped — see github_push_summary.md")
        url = git_ops.github_urls(repo_root, ls.lane.branch_name).get("branch_url")
        if url:
            lines.append(f"- GitHub: {url}")
        lines.append("")

    lines.extend(["## Branches"] + [f"- `{b}`" for b in plan.branch_names])
    lines.extend(["", "## Worktrees"] + [f"- `{w}`" for w in plan.worktree_names])

    lines.extend(["", "## Merge order"])
    for i, lane_id in enumerate(plan.merge_order, 1):
        lines.append(f"{i}. `{lane_id}`")

    lines.extend(["", "## Merge results"])
    if not session.merge_records:
        lines.append("_No merges (auto_merge=false or lanes incomplete)._")
    for mr in session.merge_records:
        st = "PASS" if mr.success else "FAIL"
        lines.append(f"- `{mr.branch}` ({mr.lane_id}): **{st}**")
        for c in mr.conflicts:
            lines.append(f"  - conflict: `{c}`")

    if session.conflict_report_path:
        lines.append(f"\nConflict report: `{session.conflict_report_path}`")

    lines.extend(["", "## Push status"])
    if not session.push_records:
        lines.append("_No pushes (auto_push_lanes=false)._")
    for pr in session.push_records:
        icon = "✅" if pr.success else "❌"
        lines.append(f"- {icon} `{pr.branch}` — {pr.output[:100]}")
        if pr.url:
            lines.append(f"  - URL: {pr.url}")

    lines.extend(["", "## Verification results"])
    for vr in session.verification_results:
        icon = "✅" if vr.success else "❌"
        cmd = vr.command if len(vr.command) <= 80 else vr.command[:77] + "..."
        lines.append(f"- {icon} **{vr.name}**: `{cmd}`")

    if session.github_urls.get("repo_url"):
        lines.extend(
            [
                "",
                "## GitHub URLs",
                f"- Repo: {session.github_urls['repo_url']}",
                f"- All branches: {session.github_urls['repo_url']}/branches",
            ]
        )
        if session.final_push and session.final_push.url:
            lines.append(f"- `{policy.base_branch}` after merge: {session.final_push.url}")

    write_github_push_report(repo_root, plan, session.push_records)

    lines.extend(["", "See also: `.parallelops/reports/github_push_summary.md`"])

    lines.extend(["", "## Final status", f"**{session.final_status}**", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
