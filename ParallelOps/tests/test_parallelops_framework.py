"""Tests for ParallelOps A1/A2 framework."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from parallelops.a1_planner import A1PlannerAgent
from parallelops.approval import is_approved, save_approval
from parallelops.models import ExecutionPlan, ExecutionPolicy
from parallelops.orchestrator import UserRequest, run_a1
from parallelops.plan_preview import build_plan_preview


class TestA1Planner(unittest.TestCase):
    def test_plan_produces_yaml_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a3-polyglot").mkdir()
            (root / "a3-polyglot" / "main.py").write_text("# api\n")
            planner = A1PlannerAgent(root)
            plan = planner.plan(
                "Extend fraud pipeline with export, thresholds, and audit log",
                max_parallel_lanes=3,
                mode="automatic",
                execution_policy=ExecutionPolicy(verification_commands=["pytest -q"]),
            )
            path = planner.save_artifact(plan)
            self.assertTrue(path.exists())
            loaded = ExecutionPlan.load(path)
            self.assertEqual(len(loaded.parallel_lanes), 3)
            self.assertEqual(loaded.version, "1.2")
            self.assertEqual(loaded.execution_policy.base_branch, "main")
            self.assertTrue(loaded.repository_analysis)

    def test_user_verification_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            planner = A1PlannerAgent(root)
            plan = planner.plan(
                "demo",
                execution_policy=ExecutionPolicy(verification_commands=["npm test", "npm run lint"]),
            )
            cmds = [s.command for s in plan.verification_plan if s.phase == "post_merge"]
            self.assertIn("npm test", cmds)
            self.assertIn("npm run lint", cmds)


class TestOrchestrator(unittest.TestCase):
    def test_a1_and_approval_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            req = UserRequest(
                task_description="Add logging",
                max_parallel_lanes=2,
                require_manual_approval=True,
            )
            result = run_a1(root, req)
            self.assertEqual(result["phase"], "a1_complete")
            preview = root / ".parallelops/reports/plan_preview.md"
            self.assertTrue(preview.exists())
            self.assertIn("Approve execution", preview.read_text())
            save_approval(root, result["session_id"])
            self.assertTrue(is_approved(root, result["session_id"]))


    def test_fullstack_repo_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DevLinker-Frontend").mkdir()
            (root / "DevLinker-backend").mkdir()
            plan = A1PlannerAgent(root).plan(
                "fix bugs and add features",
                max_parallel_lanes=3,
                execution_policy=ExecutionPolicy(auto_generate_tasks=True),
            )
            self.assertEqual(len(plan.parallel_lanes), 3)
            slugs = [lane.branch_name.split("/")[0] for lane in plan.parallel_lanes]
            self.assertIn("fix", slugs)
            self.assertIn("feature", slugs)
            self.assertIn("chore", slugs)

    def test_preview_contains_merge_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = A1PlannerAgent(root).plan("task", max_parallel_lanes=2)
            text = build_plan_preview(plan)
            self.assertIn("Merge order", text)
            self.assertIn("Risk analysis", text)


if __name__ == "__main__":
    unittest.main()
