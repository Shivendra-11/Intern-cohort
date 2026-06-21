"""Tests for eval artifact writer + dashboard index builder."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from parallelops.eval_artifacts import (
    ARTIFACT_FILES,
    BATTERY_ORDER,
    AgentResult,
    build_dashboard_from_markdown,
    build_index,
    finalize_eval,
    finish_eval_and_dashboard,
    migrate_legacy_flat_artifacts,
    record_agent_result,
    resolve_battery_agents,
    start_session,
)


class TestEvalArtifacts(unittest.TestCase):
    def _write_legacy_agent(self, root: Path, agent: str) -> None:
        dest = root / ".parallelops" / "artifacts" / agent
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "report.json").write_text(
            json.dumps(
                {
                    "agent": agent,
                    "status": "pass",
                    "summary": f"{agent} ok",
                    "charts": {"execution_metrics": [{"name": "x", "value": 1}]},
                }
            ),
            encoding="utf-8",
        )
        (dest / "report.md").write_text(f"# {agent}\n", encoding="utf-8")

    def test_start_session_writes_eval_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = start_session(root, task="demo", agents=["A1", "A2"])
            path = root / ".parallelops" / "artifacts" / "eval_session.json"
            self.assertTrue(path.exists())
            data = json.loads(path.read_text())
            self.assertEqual(data["session_id"], session.session_id)
            self.assertEqual(data["agents"], ["A1", "A2"])
            self.assertEqual(data["repo_root"], str(root.resolve()))
            self.assertEqual(data["repo_name"], root.name)
            repo_ctx = root / ".parallelops" / "artifacts" / "repo_context.json"
            self.assertTrue(repo_ctx.exists())

    def test_record_agent_writes_four_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = start_session(root, agents=["A1"])
            out = record_agent_result(
                root,
                AgentResult(agent="A1", status="pass", summary="lanes ok"),
                session_id=session.session_id,
            )
            agent_dir = root / ".parallelops" / "artifacts" / "runs" / session.session_id / "A1"
            for name in ARTIFACT_FILES:
                self.assertTrue((agent_dir / name).exists(), name)
            self.assertEqual(out["session_id"], session.session_id)
            self.assertTrue(Path(out["metadata.json"]).exists())

    def test_migrate_legacy_generates_missing_metadata_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_legacy_agent(root, "A1")
            idx = root / ".parallelops" / "artifacts" / "index.json"
            idx.parent.mkdir(parents=True, exist_ok=True)
            idx.write_text(
                json.dumps(
                    {
                        "selected_evaluation": {
                            "session_id": "sess-001",
                            "task": "test task",
                            "mode": "build+verify",
                            "overall_status": "pass",
                            "agents": ["A1"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            sid = migrate_legacy_flat_artifacts(root)
            self.assertEqual(sid, "sess-001")
            run_agent = root / ".parallelops" / "artifacts" / "runs" / "sess-001" / "A1"
            for name in ARTIFACT_FILES:
                self.assertTrue((run_agent / name).exists(), name)

    def test_finalize_builds_index_with_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_legacy_agent(root, "A1")
            self._write_legacy_agent(root, "A2")
            (root / ".parallelops" / "artifacts" / "index.json").write_text(
                json.dumps(
                    {
                        "selected_evaluation": {
                            "session_id": "sess-final",
                            "task": "battery",
                            "agents": ["A1", "A2"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            out = finalize_eval(root, session_id="sess-final")
            index_path = Path(out["index_path"])
            index = json.loads(index_path.read_text())
            self.assertEqual(index["selected_session_id"], "sess-final")
            self.assertTrue(index["sessions"])
            self.assertEqual(index["repo_root"], str(root.resolve()))
            self.assertEqual(index["repo_name"], root.name)
            self.assertEqual(index["sessions"][0]["repo_root"], str(root.resolve()))
            self.assertIn("dashboard_url", out)
            self.assertIn("localhost:3000", out["dashboard_url"])

    def test_build_dashboard_from_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            md = root / "a1-worktree-plan"
            md.mkdir(parents=True)
            (md / "decomposition.md").write_text("# A1 plan\n", encoding="utf-8")
            out = build_dashboard_from_markdown(root, agents=["A1"])
            self.assertIn("A1", out["agents_from_md"])
            sid = out["session_id"]
            bundle = root / ".parallelops" / "artifacts" / "runs" / sid / "A1"
            self.assertTrue((bundle / "report.md").exists())
            self.assertIn("localhost:3000", out["dashboard_url"])

    def test_resolve_battery_agents_all(self) -> None:
        self.assertEqual(resolve_battery_agents(["all"]), list(BATTERY_ORDER))

    def test_build_index_only_lists_agents_with_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = start_session(root, agents=["A1", "A2", "A3"])
            sid = session.session_id
            record_agent_result(
                root,
                AgentResult(agent="A2", status="pass", summary="only a2"),
                session_id=sid,
            )
            build_index(root, selected_session_id=sid)
            index = json.loads((root / ".parallelops" / "artifacts" / "index.json").read_text())
            selected = index["sessions"][0]
            self.assertEqual(selected["agents"], ["A2"])

    def test_finish_eval_and_dashboard_writes_url_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            md = root / "a1-worktree-plan"
            md.mkdir(parents=True)
            (md / "decomposition.md").write_text("# A1\n", encoding="utf-8")
            session = start_session(root, agents=["A1"])
            out = finish_eval_and_dashboard(
                root,
                session_id=session.session_id,
                agents=["A1"],
                start_server=False,
            )
            url_file = root / ".parallelops" / "artifacts" / "dashboard_url.txt"
            self.assertTrue(url_file.exists())
            self.assertIn("localhost:3000", url_file.read_text())
            self.assertIn("A1", out["agents_synced"])
            self.assertIn("session_id", out)


if __name__ == "__main__":
    unittest.main()
