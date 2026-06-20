"""Tests for lane agent dispatch."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from parallelops.a1_planner import A1PlannerAgent
from parallelops.lane_agent import build_lane_coding_prompt, write_lane_dispatch_manifest
from parallelops.models import ExecutionPolicy


class TestLaneAgent(unittest.TestCase):
    def test_dispatch_manifest_has_three_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DevLinker-Frontend").mkdir()
            (root / "DevLinker-backend").mkdir()
            planner = A1PlannerAgent(root)
            plan = planner.plan(
                "fix bugs and add features",
                max_parallel_lanes=3,
                execution_policy=ExecutionPolicy(auto_generate_tasks=True),
            )
            planner.save_artifact(plan)
            manifest = write_lane_dispatch_manifest(root, plan)
            data = json.loads(manifest.read_text())
            self.assertEqual(len(data["lanes"]), 3)
            self.assertIn("coding_prompt", data["lanes"][0])
            self.assertIn("worktree_path", data["lanes"][0])

    def test_coding_prompt_includes_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            planner = A1PlannerAgent(root)
            plan = planner.plan("demo task", max_parallel_lanes=1)
            planner.save_artifact(plan)
            lane = plan.parallel_lanes[0]
            prompt = build_lane_coding_prompt(root, plan, lane)
            self.assertIn("REAL code changes", prompt)
            self.assertIn(lane.worktree_path, prompt)


if __name__ == "__main__":
    unittest.main()
