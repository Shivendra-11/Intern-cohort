"""GitHub push summary for ParallelOps sessions."""

from __future__ import annotations

from pathlib import Path

from parallelops import git_ops
from parallelops.a2_executor import PushRecord
from parallelops.models import ExecutionPlan


def write_github_push_report(
    repo_root: Path,
    plan: ExecutionPlan,
    push_records: list[PushRecord],
) -> Path:
    """Write markdown with GitHub branch links (visible on github.com/branches)."""
    policy = plan.execution_policy
    base = policy.base_branch
    repo_url = git_ops.github_urls(repo_root, base).get("repo_url")

    pushed = {pr.branch: pr for pr in push_records}
    lines = [
        "# GitHub Push Summary",
        "",
        f"Session: `{plan.session_id}`",
        f"Repository: `{plan.task.repo_root}`",
        "",
    ]
    if repo_url:
        lines.append(f"**GitHub repo:** {repo_url}")
        lines.append(f"**All branches:** {repo_url}/branches")
        lines.append("")

    lines.extend(["## Lane branches", ""])
    for lane in plan.parallel_lanes:
        branch = lane.branch_name
        pr = pushed.get(branch)
        url = (pr.url if pr else None) or git_ops.github_urls(repo_root, branch).get("branch_url")
        compare = git_ops.github_compare_url(repo_root, base, branch)
        if pr and pr.success:
            lines.append(f"- ✅ **`{branch}`** — pushed")
        elif pr and not pr.success:
            lines.append(f"- ❌ **`{branch}`** — push failed: {pr.output[:120]}")
        else:
            lines.append(f"- ⏳ **`{branch}`** — not pushed yet")
        if url:
            lines.append(f"  - View on GitHub: {url}")
        if compare:
            lines.append(f"  - Open compare/PR: {compare}")
        lines.append("")

    final = pushed.get(base)
    lines.extend(["## Base branch", ""])
    if final and final.success:
        lines.append(f"- ✅ **`{base}`** — pushed after merge")
    elif policy.push_final_branch:
        lines.append(f"- ⏳ **`{base}`** — will push after merge (Q7 auto-push=yes)")
    else:
        lines.append("- _Base branch push disabled (enable Q7 auto-push)_")
    base_url = (final.url if final else None) or git_ops.github_urls(repo_root, base).get("branch_url")
    if base_url:
        lines.append(f"  - View on GitHub: {base_url}")

    if not repo_url:
        lines.extend(
            [
                "",
                "## Setup GitHub remote",
                "",
                "```bash",
                "git remote add origin git@github.com:ORG/REPO.git",
                "git push -u origin main",
                "```",
            ]
        )

    path = repo_root / ".parallelops/reports/github_push_summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def push_all_to_github(repo_root: Path, plan: ExecutionPlan) -> list[PushRecord]:
    """Push all lane branches + base branch; return records with GitHub URLs."""
    records: list[PushRecord] = []
    for lane in plan.parallel_lanes:
        push = git_ops.push_branch(repo_root, lane.branch_name)
        records.append(PushRecord(lane.branch_name, push.ok, push.output, push.github_url))
    base = plan.execution_policy.base_branch
    push_main = git_ops.push_branch(repo_root, base)
    records.append(PushRecord(base, push_main.ok, push_main.output, push_main.github_url))
    write_github_push_report(repo_root, plan, records)
    return records
