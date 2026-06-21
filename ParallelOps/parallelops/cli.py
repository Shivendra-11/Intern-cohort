"""CLI entry point for ParallelOps-Eval framework."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from parallelops.approval import save_approval, save_merge_approval
from parallelops.orchestrator import (
    UserRequest,
    discovery_template,
    ensure_scaffold,
    load_user_request_json,
    run_a1,
    run_a2,
    run_pipeline,
)
from parallelops.plan_preview import build_plan_preview, write_plan_preview


def _repo_root() -> Path:
    return Path.cwd()


def _request_from_args(args: argparse.Namespace) -> UserRequest:
    if getattr(args, "request", None):
        return load_user_request_json(Path(args.request))
    verify = []
    if getattr(args, "verify", None):
        verify = args.verify
    return UserRequest(
        repo_path=getattr(args, "repo", "."),
        base_branch=getattr(args, "base_branch", "main"),
        task_description=args.task,
        max_parallel_lanes=args.max_lanes,
        auto_generate_tasks=not getattr(args, "no_auto_tasks", False),
        auto_commit_lanes=args.auto_commit,
        auto_push_lanes=args.auto_push,
        require_merge_approval=not getattr(args, "no_merge_approval", False),
        worktree_base_dir=args.worktree_dir,
        branch_naming_convention=args.branch_pattern,
        artifact_location=args.artifact_dir,
        verification_commands=verify,
        run_a2=not args.plan_only,
        approved=getattr(args, "yes", False),
        dry_run=args.dry_run,
    )


def cmd_push_github(args: argparse.Namespace) -> int:
    root = _repo_root()
    from parallelops.github_push import push_all_to_github
    from parallelops.models import ExecutionPlan

    artifact = root / ".parallelops/artifacts/a1_execution_plan.yaml"
    plan = ExecutionPlan.load(artifact)
    records = push_all_to_github(root, plan)
    print(json.dumps([{"branch": r.branch, "ok": r.success, "url": r.url} for r in records], indent=2))
    print(f"\nGitHub summary: {root / '.parallelops/reports/github_push_summary.md'}")
    return 0 if all(r.success for r in records) else 1


def cmd_implement_lanes(args: argparse.Namespace) -> int:
    root = _repo_root()
    from parallelops.lane_agent import implement_lanes

    result = implement_lanes(root, use_sdk=not args.no_sdk, model=args.model)
    print(json.dumps(result, indent=2))
    if result.get("mode") == "cursor_chat_dispatch":
        print("\nNext: launch parallel lane agents in Cursor chat, then:")
        print("  python -m parallelops.cli execute")
        return 0
    return 0 if result.get("all_done") else 1


def cmd_init(_: argparse.Namespace) -> int:
    ensure_scaffold(_repo_root())
    print("ParallelOps scaffold ready under .parallelops/")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    root = _repo_root()
    ensure_scaffold(root)
    if getattr(args, "interactive", False):
        from parallelops.interactive_discover import run_interactive_discover

        run_interactive_discover(root)
        print("Next: python -m parallelops.cli plan --request .parallelops/artifacts/user_request.json")
        return 0
    out = root / ".parallelops/artifacts/user_request.json"
    out.write_text(json.dumps(discovery_template(), indent=2), encoding="utf-8")
    print(f"Discovery template: {out}")
    print("Fill in answers, then: python -m parallelops.cli plan --request .parallelops/artifacts/user_request.json")
    print("Or run discovery wizard: python -m parallelops.cli wizard")
    return 0


def cmd_wizard(_: argparse.Namespace) -> int:
    root = _repo_root()
    ensure_scaffold(root)
    from parallelops.interactive_discover import run_interactive_discover

    run_interactive_discover(root)
    print("Next: python -m parallelops.cli plan --request .parallelops/artifacts/user_request.json")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    if args.request:
        req = load_user_request_json(Path(args.request))
    else:
        req = _request_from_args(args)
    result = run_a1(_repo_root(), req)
    print(json.dumps(result, indent=2))
    print(f"\nReview: {result['plan_preview_path']}")
    print("Approve: python -m parallelops.cli approve")
    return 0


def cmd_show_plan(args: argparse.Namespace) -> int:
    root = _repo_root()
    artifact = Path(args.plan) if args.plan else root / ".parallelops/artifacts/a1_execution_plan.yaml"
    from parallelops.models import ExecutionPlan

    plan = ExecutionPlan.load(artifact)
    preview = build_plan_preview(plan)
    if args.write:
        write_plan_preview(plan, root)
    print(preview)
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    root = _repo_root()
    from parallelops.models import ExecutionPlan

    artifact = root / ".parallelops/artifacts/a1_execution_plan.yaml"
    plan = ExecutionPlan.load(artifact)
    if getattr(args, "merge", False):
        save_merge_approval(root, plan.session_id, plan.preferences.artifact_location)
        print(f"Merge approved for session {plan.session_id}")
        result = run_a2(root, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        return 0 if result.get("final_status", "").startswith("SUCCESS") else 2
    save_approval(root, plan.session_id, plan.preferences.artifact_location)
    print(f"Approved session {plan.session_id}")
    if args.execute:
        result = run_a2(
            root,
            dry_run=args.dry_run,
            skip_implementation=getattr(args, "setup_only", False),
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("final_status", "").startswith("SUCCESS") else 2
    return 0


def cmd_execute(args: argparse.Namespace) -> int:
    root = _repo_root()
    if args.skip_approval:
        from parallelops.models import ExecutionPlan

        plan = ExecutionPlan.load(
            Path(args.plan) if args.plan else root / ".parallelops/artifacts/a1_execution_plan.yaml"
        )
        save_approval(root, plan.session_id, plan.preferences.artifact_location)
    try:
        result = run_a2(root, dry_run=args.dry_run, skip_implementation=args.skip_implementation)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0 if not result.get("paused_for_conflict") else 2


def cmd_run(args: argparse.Namespace) -> int:
    req = _request_from_args(args)
    if args.request:
        req = load_user_request_json(Path(args.request))
    result = run_pipeline(_repo_root(), req)
    print(json.dumps(result, indent=2))
    if result.get("phase") == "awaiting_approval":
        print("\nAwaiting approval — run: python -m parallelops.cli approve --execute")
        return 0
    status = result.get("final_status", "")
    if result.get("paused_for_conflict"):
        return 2
    return 0 if status.startswith("SUCCESS") or result.get("phase") == "a1_only" else 1


def cmd_eval_start(args: argparse.Namespace) -> int:
    from parallelops.eval_artifacts import ensure_eval_scaffold, load_json, selection_file, start_session

    root = _repo_root()
    ensure_eval_scaffold(root)
    sel = load_json(selection_file(root))
    session = start_session(
        root,
        task=getattr(args, "task", "") or sel.get("task", "ParallelOps eval"),
        mode=getattr(args, "mode", "") or sel.get("mode", "build+verify"),
        agents=sel.get("agents"),
    )
    print(json.dumps({"session_id": session.session_id, "agents": session.agents}, indent=2))
    return 0


def cmd_eval_record(args: argparse.Namespace) -> int:
    from parallelops.eval_artifacts import AgentResult, record_agent_result

    root = _repo_root()
    result = AgentResult(
        agent=args.agent.upper(),
        status=args.status,
        mode=args.mode,
        summary=args.summary or "",
        report_md_path=args.report_md,
        report_json_path=args.report_json,
        logs_path=args.logs,
    )
    out = record_agent_result(root, result, session_id=args.session)
    print(json.dumps(out, indent=2))
    return 0


def cmd_eval_finalize(args: argparse.Namespace) -> int:
    from parallelops.eval_artifacts import finish_eval_and_dashboard

    root = _repo_root()
    out = finish_eval_and_dashboard(
        root,
        session_id=args.session,
        port=args.port,
        start_server=bool(args.dashboard),
        foreground=bool(getattr(args, "foreground", False)),
    )
    _print_dashboard_result(out, args.port)
    if args.dashboard and getattr(args, "foreground", False):
        return 0
    return 0


def cmd_eval_finish(args: argparse.Namespace) -> int:
    """Mandatory post-battery step: sync A1–A6 artifacts + launch dashboard."""
    from parallelops.eval_artifacts import finish_eval_and_dashboard

    root = _repo_root()
    agents = None
    if getattr(args, "agents", None):
        agents = [a.strip().upper() for a in args.agents.split(",") if a.strip()]
    out = finish_eval_and_dashboard(
        root,
        session_id=args.session,
        agents=agents,
        port=args.port,
        start_server=not args.no_dashboard,
        foreground=bool(args.foreground),
    )
    _print_dashboard_result(out, args.port)
    return 0


def _print_dashboard_result(out: dict, port: int) -> None:
    resolved_port = int(out.get("port", port))
    url = out.get("dashboard_url", f"http://localhost:{resolved_port}/")
    repo_name = out.get("repo_name")
    print(json.dumps(out, indent=2))
    label = f"{repo_name} " if repo_name else ""
    print(f"\nOpen {label}Dashboard: {url}\n")
    if out.get("already_running"):
        print(
            f"(Dashboard already running on port {resolved_port} for this repo — open the URL above.)\n"
        )


def cmd_eval_dashboard_from_md(args: argparse.Namespace) -> int:
    from parallelops.dashboard_server import dashboard_url, ensure_dashboard_running
    from parallelops.eval_artifacts import build_dashboard_from_markdown

    root = _repo_root()
    agents = None
    if getattr(args, "agents", None):
        agents = [a.strip().upper() for a in args.agents.split(",") if a.strip()]
    out = build_dashboard_from_markdown(root, agents=agents, session_id=args.session)
    port = args.port
    if args.dashboard:
        dash = ensure_dashboard_running(
            root,
            port=port,
            session_id=out["session_id"],
            foreground=bool(getattr(args, "foreground", False)),
        )
        out.update(dash)
        port = int(dash.get("port", port))
    url = dashboard_url(port, out["session_id"])
    out["dashboard_url"] = url
    _print_dashboard_result(out, port)
    if not out.get("agents_from_md"):
        print("Warning: no markdown reports found for any agent.", file=sys.stderr)
        return 1
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    from parallelops.dashboard_server import dashboard_url, run_dashboard_foreground

    root = _repo_root()
    session = getattr(args, "session", None)
    port = args.port
    if args.print_url:
        print(dashboard_url(port, session))
        return 0
    return run_dashboard_foreground(root, port=port, session_id=session)


def _add_common_plan_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--task", "-t", help="What changes do you want?")
    p.add_argument("--request", help="Path to user_request.json from discovery")
    p.add_argument("--repo", default=".", help="Repository path to modify")
    p.add_argument("--base-branch", default="main")
    p.add_argument("--max-lanes", type=int, default=3)
    p.add_argument("--no-auto-tasks", action="store_true", help="Do not auto-generate lane tasks")
    p.add_argument("--worktree-dir", default=".parallelops/worktrees")
    p.add_argument("--branch-pattern", default="{prefix}/{task_slug}")
    p.add_argument("--artifact-dir", default=".parallelops/artifacts")
    p.add_argument("--verify", action="append", default=[], help="Verification command (repeatable)")
    p.add_argument("--auto-commit", action="store_true")
    p.add_argument("--auto-push", action="store_true")
    p.add_argument("--no-merge-approval", action="store_true", help="Merge to main without extra gate")
    p.add_argument("--plan-only", action="store_true")
    p.add_argument("--yes", "-y", action="store_true", help="Skip execution approval gate")
    p.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="parallelops", description="ParallelOps-Eval A1/A2 orchestrator")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create .parallelops/ scaffold").set_defaults(func=cmd_init)

    disc_p = sub.add_parser("discover", help="Write user_request.json discovery template")
    disc_p.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Ask all 14 discovery questions in the terminal",
    )
    disc_p.set_defaults(func=cmd_discover)

    sub.add_parser("wizard", help="Interactive terminal wizard (9 questions)").set_defaults(
        func=cmd_wizard
    )

    impl_p = sub.add_parser(
        "implement-lanes",
        help="Run coding agents in each worktree lane (Cursor SDK or dispatch manifest)",
    )
    impl_p.add_argument("--no-sdk", action="store_true", help="Only write lane_dispatch.json")
    impl_p.add_argument("--model", default="composer-2.5")
    impl_p.set_defaults(func=cmd_implement_lanes)

    push_p = sub.add_parser(
        "push-github",
        help="Push all lane branches + main to origin (visible on GitHub)",
    )
    push_p.set_defaults(func=cmd_push_github)

    plan_p = sub.add_parser("plan", help="Phase 3: A1 plan only")
    _add_common_plan_flags(plan_p)
    plan_p.set_defaults(func=cmd_plan)

    show_p = sub.add_parser("show-plan", help="Phase 4: display plan for approval")
    show_p.add_argument("--plan", help="Path to a1_execution_plan.yaml")
    show_p.add_argument("--write", action="store_true", help="Write plan_preview.md")
    show_p.set_defaults(func=cmd_show_plan)

    appr_p = sub.add_parser("approve", help="Approve plan and optionally execute A2")
    appr_p.add_argument("--execute", action="store_true")
    appr_p.add_argument(
        "--setup-only",
        action="store_true",
        help="Create branches/worktrees only; lane agents write code next",
    )
    appr_p.add_argument("--merge", action="store_true", help="Approve merge to main and continue A2")
    appr_p.add_argument("--dry-run", action="store_true")
    appr_p.set_defaults(func=cmd_approve)

    exec_p = sub.add_parser("execute", help="Phase 5: A2 execute (requires approval)")
    exec_p.add_argument("--plan", help="Path to a1_execution_plan.yaml")
    exec_p.add_argument("--skip-approval", action="store_true")
    exec_p.add_argument("--dry-run", action="store_true")
    exec_p.add_argument("--skip-implementation", action="store_true")
    exec_p.set_defaults(func=cmd_execute)

    run_p = sub.add_parser("run", help="Full pipeline: discover → A1 → [approve] → A2")
    _add_common_plan_flags(run_p)
    run_p.set_defaults(func=cmd_run)

    est_p = sub.add_parser("eval-start", help="Start eval session (writes eval_session.json)")
    est_p.add_argument("--task", default="")
    est_p.add_argument("--mode", default="build+verify")
    est_p.set_defaults(func=cmd_eval_start)

    rec_p = sub.add_parser("eval-record", help="Record one agent result + four-file artifact bundle")
    rec_p.add_argument("--agent", required=True, help="A1–A6")
    rec_p.add_argument("--status", default="pass", choices=["pass", "fail", "partial", "skipped"])
    rec_p.add_argument("--mode", default="build+verify")
    rec_p.add_argument("--summary", default="")
    rec_p.add_argument("--session", help="Session id (default: current eval_session.json)")
    rec_p.add_argument("--report-md", dest="report_md", help="Path to report.md to copy")
    rec_p.add_argument("--report-json", dest="report_json", help="Path to report.json to merge")
    rec_p.add_argument("--logs", help="Path to logs.txt to copy")
    rec_p.set_defaults(func=cmd_eval_record)

    fin_p = sub.add_parser(
        "eval-finalize",
        help="Build runs/{session}/ artifacts + index.json for dashboard",
    )
    fin_p.add_argument("--session", help="Session id (default: current)")
    fin_p.add_argument("--port", type=int, default=3000)
    fin_p.add_argument(
        "--dashboard",
        action="store_true",
        help="Start dashboard server after finalize",
    )
    fin_p.add_argument(
        "--foreground",
        action="store_true",
        help="Run dashboard in foreground (blocks terminal)",
    )
    fin_p.set_defaults(func=cmd_eval_finalize)

    finish_p = sub.add_parser(
        "eval-finish",
        help="After A1–A6 battery: sync artifacts, rebuild index, launch dashboard (recommended)",
    )
    finish_p.add_argument("--session", help="Session id (default: current eval_session.json)")
    finish_p.add_argument(
        "--agents",
        help="Comma-separated agents (default: from eval_selection.json or full battery)",
    )
    finish_p.add_argument("--port", type=int, default=3000)
    finish_p.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Build artifacts only; do not start the dev server",
    )
    finish_p.add_argument(
        "--foreground",
        action="store_true",
        help="Run dashboard in foreground (blocks terminal)",
    )
    finish_p.set_defaults(func=cmd_eval_finish)

    md_p = sub.add_parser(
        "eval-dashboard-from-md",
        help="Build dashboard from existing A1–A6 markdown reports (no agent run)",
    )
    md_p.add_argument("--session", help="Optional session id")
    md_p.add_argument(
        "--agents",
        help="Comma-separated agents to ingest (default: A1–A6)",
    )
    md_p.add_argument("--port", type=int, default=3000)
    md_p.add_argument(
        "--dashboard",
        action="store_true",
        help="Start dashboard server after building artifacts",
    )
    md_p.set_defaults(func=cmd_eval_dashboard_from_md)

    dash_p = sub.add_parser("dashboard", help="Start eval dashboard on localhost")
    dash_p.add_argument("--port", type=int, default=3000)
    dash_p.add_argument("--session", help="Pre-select session in URL")
    dash_p.add_argument("--print-url", action="store_true", help="Print URL only")
    dash_p.set_defaults(func=cmd_dashboard)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in ("plan", "run") and not args.request and not getattr(args, "task", None):
        parser.error("--task or --request required")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
