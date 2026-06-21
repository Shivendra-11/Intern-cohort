"""A2ExecutorAgent — execute A1 plan exactly; never replans."""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from parallelops import git_ops
from parallelops.approval import is_merge_approved
from parallelops.models import ExecutionPlan, ParallelLane


class LaneStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LaneSession:
    lane: ParallelLane
    status: LaneStatus = LaneStatus.PENDING
    commits: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    log_path: str = ""
    error: str = ""
    pushed: bool = False
    push_log: str = ""


@dataclass
class MergeRecord:
    branch: str
    lane_id: str
    success: bool
    conflicts: list[str] = field(default_factory=list)
    resolution_notes: str = ""


@dataclass
class PushRecord:
    branch: str
    success: bool
    output: str
    url: str | None = None


@dataclass
class VerificationResult:
    name: str
    command: str
    success: bool
    output: str


@dataclass
class ExecutionSession:
    plan: ExecutionPlan
    session_dir: Path
    lanes: list[LaneSession] = field(default_factory=list)
    merge_records: list[MergeRecord] = field(default_factory=list)
    push_records: list[PushRecord] = field(default_factory=list)
    verification_results: list[VerificationResult] = field(default_factory=list)
    paused_for_conflict: bool = False
    conflict_report_path: str = ""
    final_push: PushRecord | None = None
    github_urls: dict[str, str | None] = field(default_factory=dict)
    final_status: str = "PENDING"


class A2ExecutorAgent:
    """Consumes `.parallelops/artifacts/a1_execution_plan.yaml` and executes it."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def load_plan(self, artifact_path: Path | None = None) -> ExecutionPlan:
        if artifact_path is None:
            artifact_path = self.repo_root / ".parallelops/artifacts/a1_execution_plan.yaml"
        if not artifact_path.exists():
            raise FileNotFoundError(
                f"A1 artifact not found: {artifact_path}. Run A1 planner first."
            )
        return ExecutionPlan.load(artifact_path)

    def execute(
        self,
        plan: ExecutionPlan,
        *,
        dry_run: bool = False,
        skip_lane_implementation: bool = False,
    ) -> ExecutionSession:
        policy = plan.execution_policy
        base = policy.base_branch
        session_dir = self.repo_root / ".parallelops/sessions" / plan.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = self.repo_root / ".parallelops/logs" / plan.session_id
        logs_dir.mkdir(parents=True, exist_ok=True)

        session = ExecutionSession(plan=plan, session_dir=session_dir)
        session.lanes = [LaneSession(lane=lane) for lane in plan.parallel_lanes]
        session.github_urls = git_ops.github_urls(self.repo_root, base)

        (session_dir / "plan_snapshot.json").write_text(
            json.dumps(plan.to_dict(), indent=2), encoding="utf-8"
        )

        if dry_run:
            self._log(session, "DRY RUN — would create worktrees and execute lanes")
            session.final_status = "DRY_RUN"
            return session

        git_ops.ensure_git_repo(self.repo_root)

        # Step 1–3: create worktrees and run lane agents (parallel where possible)
        def _run_lane(ls: LaneSession) -> None:
            ls.status = LaneStatus.RUNNING
            wt_path = self._resolve_worktree_path(ls.lane.worktree_path)
            log_file = logs_dir / f"{ls.lane.id}_worktree.log"
            try:
                result = git_ops.create_worktree(
                    self.repo_root, wt_path, ls.lane.branch_name, base_branch=base
                )
                log_file.write_text(result.text(), encoding="utf-8")
                ls.log_path = str(log_file)

                prompt_path = session_dir / ls.lane.id / "agent_prompt.md"
                prompt_path.parent.mkdir(parents=True, exist_ok=True)
                prompt_path.write_text(plan.agent_prompts[ls.lane.id], encoding="utf-8")

                if not skip_lane_implementation:
                    self._run_lane_implementation(ls, wt_path, session_dir, logs_dir, plan)

                ls.commits = self._list_commits(wt_path, ls.lane.branch_name)
                ls.changed_files = git_ops.get_changed_files(
                    self.repo_root, ls.lane.branch_name, base=base
                )

                ls.status = LaneStatus.COMPLETED
            except Exception as exc:  # noqa: BLE001
                ls.status = LaneStatus.FAILED
                ls.error = str(exc)
                (logs_dir / f"{ls.lane.id}_error.log").write_text(str(exc), encoding="utf-8")

        with ThreadPoolExecutor(max_workers=len(session.lanes) or 1) as pool:
            futures = {pool.submit(_run_lane, ls): ls for ls in session.lanes}
            for fut in as_completed(futures):
                fut.result()

        if policy.auto_push_lanes and not session.paused_for_conflict:
            self._push_lane_branches_to_github(session, logs_dir)

        # Step 5: verification (before merge when require_merge_approval defers merge)
        awaiting_merge = policy.require_merge_approval and not is_merge_approved(
            self.repo_root, plan.session_id, plan.preferences.artifact_location
        )

        if not session.paused_for_conflict:
            self._verify(session, logs_dir)

        # Step 6: merge in A1 order (skip if merge approval pending)
        if policy.auto_merge and not session.paused_for_conflict and not awaiting_merge:
            self._reconcile(session, logs_dir, base, policy.pause_on_conflict)
        elif awaiting_merge:
            self._log(
                session,
                "Merge paused — require_merge_approval=true. "
                "Run: python -m parallelops.cli approve --merge",
            )
            session.final_status = "PENDING — awaiting merge approval"

        # Step 7: push main to GitHub after successful merge
        if (
            policy.push_final_branch
            and not session.paused_for_conflict
            and not awaiting_merge
            and session.merge_records
            and all(m.success for m in session.merge_records)
        ):
            push = git_ops.push_branch(self.repo_root, base)
            session.final_push = PushRecord(base, push.ok, push.output, push.github_url)
            session.push_records.append(session.final_push)
            (logs_dir / "push_final.log").write_text(push.output, encoding="utf-8")
        elif (
            policy.push_final_branch
            and not session.paused_for_conflict
            and not awaiting_merge
            and not session.merge_records
            and policy.auto_push_lanes
        ):
            # Lanes pushed but merge skipped — still push updated base if checked out
            push = git_ops.push_branch(self.repo_root, base)
            if push.ok:
                session.final_push = PushRecord(base, push.ok, push.output, push.github_url)
                session.push_records.append(session.final_push)

        if session.final_status.startswith("PENDING"):
            pass
        else:
            session.final_status = self._compute_status(session)
        return session

    def _push_lane_branches_to_github(
        self,
        session: ExecutionSession,
        logs_dir: Path,
        *,
        skip_if_pushed: bool = False,
    ) -> None:
        """Push all lane branches so they appear on github.com under Branches."""
        already = {pr.branch for pr in session.push_records if pr.success}
        for ls in session.lanes:
            if ls.status != LaneStatus.COMPLETED:
                continue
            if skip_if_pushed and ls.lane.branch_name in already:
                continue
            push = git_ops.push_branch(self.repo_root, ls.lane.branch_name)
            ls.pushed = push.ok
            ls.push_log = push.output
            session.push_records.append(
                PushRecord(ls.lane.branch_name, push.ok, push.output, push.github_url)
            )
            (logs_dir / f"{ls.lane.id}_push_github.log").write_text(push.output, encoding="utf-8")

    def _resolve_worktree_path(self, configured: str) -> Path:
        p = Path(configured)
        if not p.is_absolute():
            p = self.repo_root / p
        return p.resolve()

    def _run_lane_implementation(
        self,
        ls: LaneSession,
        wt_path: Path,
        session_dir: Path,
        logs_dir: Path,
        plan: ExecutionPlan,
    ) -> None:
        policy = plan.execution_policy
        lane_out = session_dir / ls.lane.id
        lane_out.mkdir(parents=True, exist_ok=True)

        if plan.task.mode == "interactive" and not policy.auto_commit_lanes:
            (lane_out / "README.md").write_text(
                f"""# Lane {ls.lane.id} — awaiting agent

Worktree: `{wt_path}`
Branch: `{ls.lane.branch_name}`

Open `agent_prompt.md` in a Cursor agent. Commit when done.
A2 merges when you re-run execute after all lanes complete.
""",
                encoding="utf-8",
            )
            return

        for owned in ls.lane.files_owned:
            target = wt_path / owned
            if owned.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                (target / ".parallelops_lane_marker").write_text(
                    f"lane={ls.lane.id}\ngoal={ls.lane.goal}\n", encoding="utf-8"
                )
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    if owned.endswith(".py"):
                        target.write_text(
                            f'"""Scaffold for {ls.lane.name} — {ls.lane.goal}"""\n',
                            encoding="utf-8",
                        )
                    elif owned.endswith(".json"):
                        target.write_text("{}\n", encoding="utf-8")
                    else:
                        target.write_text(
                            f"# {ls.lane.name}\n\nScaffold by A2.\n", encoding="utf-8"
                        )

        git_ops.run_git(wt_path, "add", "-A")
        commit_hint = next(
            (d.replace("Commit: `", "").rstrip("`") for d in ls.lane.deliverables if d.startswith("Commit:")),
            f"feat({ls.lane.worktree_name}): lane implementation",
        )
        commit_result = git_ops.run_git(wt_path, "commit", "-m", commit_hint)
        if not commit_result.ok:
            git_ops.run_git(wt_path, "commit", "-m", commit_hint, "--allow-empty")
        (logs_dir / f"{ls.lane.id}_implement.log").write_text(commit_result.text(), encoding="utf-8")

    def _list_commits(self, wt_path: Path, branch: str) -> list[str]:
        result = git_ops.run_git(wt_path, "log", "--oneline", "-5", branch)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def _reconcile(
        self, session: ExecutionSession, logs_dir: Path, target: str, pause_on_conflict: bool
    ) -> None:
        branches = git_ops.run_git(self.repo_root, "branch", "--list").stdout
        if target not in branches and "master" in branches:
            target = "master"

        for lane_id in session.plan.merge_order:
            ls = next((x for x in session.lanes if x.lane.id == lane_id), None)
            if not ls or ls.status != LaneStatus.COMPLETED:
                continue
            merge_log = logs_dir / f"merge_{lane_id}.log"
            try:
                result = git_ops.merge_branch(self.repo_root, ls.lane.branch_name, target)
                merge_log.write_text(result.text(), encoding="utf-8")
                conflicts = git_ops.list_conflicts(self.repo_root)
                record = MergeRecord(
                    branch=ls.lane.branch_name,
                    lane_id=lane_id,
                    success=result.ok and not conflicts,
                    conflicts=conflicts,
                )
                if conflicts:
                    report_path = (
                        self.repo_root
                        / ".parallelops/reports"
                        / f"conflict_{session.plan.session_id}.md"
                    )
                    report_path.parent.mkdir(parents=True, exist_ok=True)
                    report_path.write_text(self._conflict_report(session, record), encoding="utf-8")
                    session.conflict_report_path = str(report_path)
                    record.resolution_notes = "Conflict detected during merge"
                    if pause_on_conflict:
                        session.paused_for_conflict = True
                        session.merge_records.append(record)
                        break
                session.merge_records.append(record)
            except Exception as exc:  # noqa: BLE001
                session.merge_records.append(
                    MergeRecord(
                        branch=ls.lane.branch_name,
                        lane_id=lane_id,
                        success=False,
                        resolution_notes=str(exc),
                    )
                )
                if pause_on_conflict:
                    session.paused_for_conflict = True
                    break

        if not session.paused_for_conflict:
            for ls in session.lanes:
                wt = self._resolve_worktree_path(ls.lane.worktree_path)
                git_ops.remove_worktree(self.repo_root, wt)

    def _conflict_report(self, session: ExecutionSession, record: MergeRecord) -> str:
        lines = [
            "# ParallelOps Conflict Report",
            "",
            f"Session: `{session.plan.session_id}`",
            f"Branch: `{record.branch}`",
            f"Lane: `{record.lane_id}`",
            "",
            "## Conflicting files",
        ]
        for f in record.conflicts:
            lines.append(f"- `{f}`")
        lines.extend(
            [
                "",
                "## Suggested resolution",
                "1. Resolve conflicts in repo root",
                "2. `git add` && `git commit`",
                "3. Re-run: `python -m parallelops.cli execute`",
                "",
            ]
        )
        return "\n".join(lines)

    def _verify(self, session: ExecutionSession, logs_dir: Path) -> None:
        for step in session.plan.verification_plan:
            if step.phase == "manual":
                session.verification_results.append(
                    VerificationResult(step.name, step.command, True, "skipped (manual)")
                )
                continue
            if session.paused_for_conflict and step.phase == "post_merge":
                session.verification_results.append(
                    VerificationResult(step.name, step.command, False, "skipped — merge paused")
                )
                continue
            try:
                proc = subprocess.run(
                    step.command,
                    shell=True,
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                ok = proc.returncode == 0 or (
                    step.name == "git_status_clean" and not step.required
                )
                out = (proc.stdout or "") + (proc.stderr or "")
                session.verification_results.append(
                    VerificationResult(step.name, step.command, ok, out[:4000])
                )
                (logs_dir / f"verify_{step.name}.log").write_text(out, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                session.verification_results.append(
                    VerificationResult(step.name, step.command, False, str(exc))
                )

    def _compute_status(self, session: ExecutionSession) -> str:
        if session.paused_for_conflict:
            return "FAILURE — paused for conflict"
        all_lanes_ok = all(lane.status == LaneStatus.COMPLETED for lane in session.lanes)
        verify_ok = all(
            v.success
            for v in session.verification_results
            if v.name not in ("manual_smoke", "git_status_clean")
        )
        merge_ok = all(m.success for m in session.merge_records) if session.merge_records else True
        if all_lanes_ok and merge_ok and verify_ok:
            return "SUCCESS"
        if all_lanes_ok and merge_ok:
            return "SUCCESS — verify warnings"
        return "FAILURE"

    def _log(self, session: ExecutionSession, message: str) -> None:
        log = session.session_dir / "executor.log"
        ts = datetime.now(timezone.utc).isoformat()
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
