"""A1PlannerAgent — decompose tasks into parallel lanes; never edits code or branches."""

from __future__ import annotations

import re
from pathlib import Path

from parallelops.models import (
    ExecutionPlan,
    ExecutionPolicy,
    OwnershipRule,
    ParallelLane,
    RiskItem,
    TaskSpec,
    UserPreferences,
    VerificationStep,
    new_session_id,
)
from parallelops.repo_analysis import analyze_repository
from parallelops.repo_scanner import suggest_lane_templates


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:32] or "task"


def _branch_name(tmpl: dict[str, str], task_slug: str, convention: str) -> str:
    prefix = tmpl.get("prefix", "feature")
    slug = tmpl.get("slug", "lane")
    if "{prefix}" in convention:
        return convention.replace("{prefix}", prefix).replace("{task_slug}", task_slug).replace(
            "{lane_slug}", slug
        )
    return f"{prefix}/{task_slug}-{slug}"


def _worktree_name(repo_root: Path, lane_slug: str) -> str:
    repo_slug = _slugify(repo_root.name) or "repo"
    short = {"fix": "fix", "feature": "feature", "tests": "tests"}.get(lane_slug, lane_slug)
    return f"{repo_slug}-{short}"


def _ownership_for_lane(
    lane_slug: str,
    repo_root: Path,
    analysis: dict,
) -> tuple[list[str], list[str]]:
    """Repo-agnostic ownership from analysis hints."""
    hints = analysis.get("ownership_hints", {})
    polyglot = repo_root / "a3-polyglot"

    if polyglot.exists():
        mapping = {
            "fix": (["a3-polyglot/worker/", "a3-polyglot/fraud-engine/"], ["a3-polyglot/main.py"]),
            "feature": (["a3-polyglot/routers/", "a3-polyglot/main.py"], ["a3-polyglot/contract.md"]),
            "tests": (["a3-polyglot/tests/", "tests/"], ["a3-polyglot/fraud-engine/"]),
            "export": (
                ["a3-polyglot/routers/export.py", "a3-polyglot/tests/test_export.py"],
                ["a3-polyglot/main.py", "a3-polyglot/contract.md"],
            ),
            "thresholds": (
                ["a3-polyglot/routers/thresholds.py", "a3-polyglot/tests/test_thresholds.py"],
                ["a3-polyglot/main.py"],
            ),
            "audit": (
                ["a3-polyglot/routers/audit.py", "a3-polyglot/tests/test_audit.py"],
                ["a3-polyglot/main.py"],
            ),
        }
        if lane_slug in mapping:
            return mapping[lane_slug]

    lane_map = {
        "fix": ("api", ["backend", "server", "api", "src/"]),
        "feature": ("ui", ["frontend", "ui", "src/components", "client"]),
        "tests": ("tests", ["tests", "test", "docs", "README.md"]),
    }
    key, fallbacks = lane_map.get(lane_slug, ("api", []))
    owned: list[str] = list(hints.get(key, []))
    for fb in fallbacks:
        p = repo_root / fb.split("/")[0]
        if p.exists() and fb not in owned:
            owned.append(fb if fb.endswith("/") or "." in fb else f"{fb}/")

    if not owned:
        owned = [f".parallelops/sessions/lane_{lane_slug}/"]

    forbidden: list[str] = []
    for other_key, other_paths in hints.items():
        if other_key != key:
            forbidden.extend(other_paths)
    forbidden = list(dict.fromkeys(forbidden))
    return owned, forbidden


def _build_agent_prompt(
    lane: ParallelLane,
    task: TaskSpec,
    constraints: dict,
    commit_hint: str,
) -> str:
    owned = "\n".join(f"- `{p}`" for p in lane.files_owned) or "- (none specified)"
    forbidden = "\n".join(f"- `{p}`" for p in lane.files_forbidden) or "- (none specified)"
    criteria = "\n".join(f"- {c}" for c in lane.success_criteria)
    deliverables = "\n".join(f"- {d}" for d in lane.deliverables)

    return f"""# Lane Agent Prompt — {lane.name}

## Context
Lane **{lane.id}** on branch `{lane.branch_name}`.
Repository: `{task.repo_root}`

**A2 dispatched this from the A1 plan. Do not replan — implement only this lane.**

## Goal
{lane.goal}

## Allowed directories (files_owned)
{owned}

## Forbidden directories (do not touch)
{forbidden}

## Deliverables
{deliverables}

## Success criteria
{criteria}

## Shared constraints
- No dependency upgrades unless required for the lane goal
- Preserve API contracts across lanes
- No cross-lane file ownership
- Commit message hint: `{commit_hint}`
- Lint/test owned modules before marking complete

## Instructions
1. Work in worktree `{lane.worktree_path}` on branch `{lane.branch_name}`.
2. Make **real code changes** in owned paths.
3. Commit: `{commit_hint}`
4. Push branch when done (if auto-push enabled).
5. Do not merge — A2 merges in plan order after verification.
"""


def _build_risk_plan(lanes: list[ParallelLane]) -> list[RiskItem]:
    risks: list[RiskItem] = []
    all_owned: dict[str, str] = {}
    for lane in lanes:
        for path in lane.files_owned:
            if path in all_owned:
                risks.append(
                    RiskItem(
                        category="shared_file_overlap",
                        description=f"`{path}` claimed by {all_owned[path]} and {lane.id}",
                        mitigation="Revise ownership in A1 plan before execution",
                        affected_lanes=[all_owned[path], lane.id],
                    )
                )
            all_owned[path] = lane.id

    hot_files = ["package.json", "package-lock.json", "README.md", "main.py"]
    for hot in hot_files:
        risks.append(
            RiskItem(
                category="integrator_file",
                description=f"`{hot}` may need sequential integrator edits after lane merges",
                mitigation="Merge lanes in merge_order; resolve conflicts before push to main",
                affected_lanes=[lane.id for lane in lanes],
            )
        )
    return risks


def _build_verification_plan(
    repo_root: Path,
    analysis: dict,
    user_commands: list[str] | None = None,
) -> list[VerificationStep]:
    steps: list[VerificationStep] = []
    commands = user_commands or analysis.get("recommended_verification", [])
    for i, cmd in enumerate(commands, start=1):
        if cmd.startswith("echo "):
            continue
        name = re.sub(r"[^a-z0-9_]+", "_", cmd.split()[0].lower())[:32] or f"verify_{i}"
        steps.append(VerificationStep(name=name, command=cmd, phase="post_merge"))
    if not steps:
        steps.append(
            VerificationStep(
                name="git_status",
                command="git status --porcelain",
                phase="post_merge",
                required=False,
            )
        )
    return steps


class A1PlannerAgent:
    """Plans parallel lanes; writes `.parallelops/artifacts/a1_execution_plan.yaml`."""

    ARTIFACT_NAME = "a1_execution_plan.yaml"

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def plan(
        self,
        task_description: str,
        *,
        mode: str = "interactive",
        single_or_multi: str = "multi",
        can_parallelize: bool = True,
        max_parallel_lanes: int = 3,
        auto_generate_tasks: bool = True,
        worktree_base_dir: str = ".parallelops/worktrees",
        branch_naming_convention: str = "{prefix}/{task_slug}",
        artifact_location: str = ".parallelops/artifacts",
        execution_policy: ExecutionPolicy | None = None,
    ) -> ExecutionPlan:
        repo_analysis = analyze_repository(self.repo_root)
        policy = execution_policy or ExecutionPolicy()

        if not can_parallelize or single_or_multi == "single":
            max_lanes = 1
        else:
            max_lanes = max_parallel_lanes

        task_slug = _slugify(task_description.split(",")[0].split(" to ")[0])
        templates = suggest_lane_templates(
            task_description,
            repo_analysis,
            max_lanes,
            auto_generate=policy.auto_generate_tasks if policy else auto_generate_tasks,
        )
        if single_or_multi == "single" or not can_parallelize:
            templates = templates[:1]

        preferences = UserPreferences(
            max_parallel_lanes=max_parallel_lanes,
            worktree_base_dir=worktree_base_dir,
            branch_naming_convention=branch_naming_convention,
            artifact_location=artifact_location,
        )

        lanes: list[ParallelLane] = []
        agent_prompts: dict[str, str] = {}
        ownership_rules: list[OwnershipRule] = []
        commit_hints: dict[str, str] = {}

        for i, tmpl in enumerate(templates, start=1):
            lane_id = f"lane_{i}"
            lane_slug = tmpl["slug"]
            branch = _branch_name(tmpl, task_slug, branch_naming_convention)
            wt_name = _worktree_name(self.repo_root, lane_slug)
            wt_path = str(Path(worktree_base_dir) / wt_name)
            owned, forbidden = _ownership_for_lane(lane_slug, self.repo_root, repo_analysis)

            commit_prefix = tmpl.get("commit_prefix", "feat")
            commit_hint = {
                "fix": f"fix: resolve {task_slug} issues",
                "feature": f"feat: add {task_slug} support",
                "tests": f"test: add coverage and docs for {task_slug}",
            }.get(lane_slug, f"{commit_prefix}: {task_slug}")

            lane = ParallelLane(
                id=lane_id,
                name=tmpl["name"],
                branch_name=branch,
                worktree_name=wt_name,
                worktree_path=wt_path,
                goal=tmpl["goal"],
                files_owned=owned,
                files_forbidden=forbidden,
                deliverables=[
                    f"Real code changes in: {', '.join(owned[:3])}",
                    f"Commit: `{commit_hint}`",
                    "Push branch when complete",
                ],
                success_criteria=[
                    "Real coding work completed (not scaffold-only)",
                    "Changes only in files_owned",
                    f"Commit present: `{commit_hint}`",
                    "Lane-owned tests pass if applicable",
                ],
            )
            lanes.append(lane)
            commit_hints[lane_id] = commit_hint
            ownership_rules.append(OwnershipRule(lane_id=lane_id, owns=owned, forbidden=forbidden))

        shared_constraints = {
            "no_dependency_upgrades": "Do not bump shared deps from lane branches",
            "preserve_api_contracts": True,
            "no_cross_lane_ownership": True,
            "commit_convention": "fix|feat|test: imperative summary per lane",
            "verification": "Run lint, build, tests after merge to main",
        }

        for lane in lanes:
            agent_prompts[lane.id] = _build_agent_prompt(
                lane,
                TaskSpec(description=task_description, mode=mode, repo_root=str(self.repo_root)),
                shared_constraints,
                commit_hints[lane.id],
            )

        merge_order = [lane.id for lane in lanes]
        verify_cmds = policy.verification_commands or repo_analysis.get("recommended_verification", [])

        from datetime import datetime, timezone

        plan = ExecutionPlan(
            version="1.2",
            session_id=new_session_id(),
            created_at=datetime.now(timezone.utc).isoformat(),
            task=TaskSpec(
                description=task_description,
                mode=mode,
                repo_root=str(self.repo_root),
                single_or_multi=single_or_multi,
                can_parallelize=can_parallelize,
            ),
            preferences=preferences,
            execution_policy=policy,
            parallel_lanes=lanes,
            branch_names=[lane.branch_name for lane in lanes],
            worktree_names=[lane.worktree_name for lane in lanes],
            agent_prompts=agent_prompts,
            shared_constraints=shared_constraints,
            ownership_rules=ownership_rules,
            merge_order=merge_order,
            risk_plan=_build_risk_plan(lanes),
            verification_plan=_build_verification_plan(self.repo_root, repo_analysis, verify_cmds),
            repository_metadata=repo_analysis,
            repository_analysis=repo_analysis,
        )
        return plan

    def save_artifact(self, plan: ExecutionPlan) -> Path:
        artifact_dir = self.repo_root / plan.preferences.artifact_location
        path = artifact_dir / self.ARTIFACT_NAME
        plan.save(path)
        prompts_dir = artifact_dir / "lane_prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        for lane_id, prompt in plan.agent_prompts.items():
            (prompts_dir / f"{lane_id}.prompt.md").write_text(prompt, encoding="utf-8")
        return path
