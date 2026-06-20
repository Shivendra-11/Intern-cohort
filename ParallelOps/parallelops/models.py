"""Data models and YAML serialization for A1 execution plans."""

from __future__ import annotations

import dataclasses
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _filter_fields(cls: type, raw: dict[str, Any]) -> dict[str, Any]:
    names = {f.name for f in dataclasses.fields(cls)}
    return {k: v for k, v in raw.items() if k in names}


@dataclass
class TaskSpec:
    description: str
    mode: str  # interactive | automatic
    repo_root: str
    single_or_multi: str = "multi"  # single | multi
    can_parallelize: bool = True


@dataclass
class ExecutionPolicy:
    base_branch: str = "main"
    auto_generate_tasks: bool = True
    auto_commit_lanes: bool = False
    auto_push_lanes: bool = False
    auto_merge: bool = True
    pause_on_conflict: bool = True
    push_final_branch: bool = False
    require_manual_approval: bool = True
    require_merge_approval: bool = True
    verification_commands: list[str] = field(default_factory=list)


@dataclass
class UserPreferences:
    max_parallel_lanes: int = 3
    worktree_base_dir: str = ".parallelops/worktrees"
    branch_naming_convention: str = "feature/{task_slug}-{lane_slug}"
    artifact_location: str = ".parallelops/artifacts"
    output_artifact_location: str = ".parallelops/reports"


@dataclass
class ParallelLane:
    id: str
    name: str
    branch_name: str
    worktree_name: str
    worktree_path: str
    goal: str
    files_owned: list[str] = field(default_factory=list)
    files_forbidden: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class OwnershipRule:
    lane_id: str
    owns: list[str]
    forbidden: list[str]


@dataclass
class RiskItem:
    category: str
    description: str
    mitigation: str
    affected_lanes: list[str] = field(default_factory=list)


@dataclass
class VerificationStep:
    name: str
    command: str
    required: bool = True
    phase: str = "post_merge"  # per_lane | post_merge | manual


@dataclass
class ExecutionPlan:
    version: str
    session_id: str
    created_at: str
    task: TaskSpec
    preferences: UserPreferences
    execution_policy: ExecutionPolicy
    parallel_lanes: list[ParallelLane]
    branch_names: list[str]
    worktree_names: list[str]
    agent_prompts: dict[str, str]
    shared_constraints: dict[str, Any]
    ownership_rules: list[OwnershipRule]
    merge_order: list[str]
    risk_plan: list[RiskItem]
    verification_plan: list[VerificationStep]
    repository_metadata: dict[str, Any] = field(default_factory=dict)
    repository_analysis: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(self.to_dict(), sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, path: Path) -> ExecutionPlan:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        policy_raw = raw.get("execution_policy") or {}
        return cls(
            version=raw.get("version", "1.0"),
            session_id=raw["session_id"],
            created_at=raw["created_at"],
            task=TaskSpec(**_filter_fields(TaskSpec, raw["task"])),
            preferences=UserPreferences(**_filter_fields(UserPreferences, raw["preferences"])),
            execution_policy=ExecutionPolicy(**_filter_fields(ExecutionPolicy, policy_raw)),
            parallel_lanes=[ParallelLane(**lane) for lane in raw["parallel_lanes"]],
            branch_names=raw["branch_names"],
            worktree_names=raw["worktree_names"],
            agent_prompts=raw["agent_prompts"],
            shared_constraints=raw["shared_constraints"],
            ownership_rules=[OwnershipRule(**r) for r in raw["ownership_rules"]],
            merge_order=raw["merge_order"],
            risk_plan=[RiskItem(**r) for r in raw["risk_plan"]],
            verification_plan=[VerificationStep(**s) for s in raw["verification_plan"]],
            repository_metadata=raw.get("repository_metadata", {}),
            repository_analysis=raw.get("repository_analysis", {}),
        )


def new_session_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
