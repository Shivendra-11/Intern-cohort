"""Interactive terminal wizard — 9 discovery questions (ParallelOps-Eval v2)."""

from __future__ import annotations

from pathlib import Path

from parallelops.orchestrator import UserRequest, save_user_request_json


def _prompt(text: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{text}{suffix}: ").strip()
    return value or default


def _yes_no(text: str, default: bool = True) -> bool:
    default_s = "yes" if default else "no"
    while True:
        value = input(f"{text} (yes/no) [{default_s}]: ").strip().lower()
        if not value:
            return default
        if value in ("yes", "y", "true", "1"):
            return True
        if value in ("no", "n", "false", "0"):
            return False
        print("  Please enter yes or no.")


def _verify_commands() -> list[str]:
    print("\nVerification commands (empty line to finish):")
    print("  Examples: npm run lint | npm run build | npm test")
    cmds: list[str] = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        cmds.append(line)
    return cmds


def run_interactive_discover(repo_root: Path | None = None) -> UserRequest:
    """Ask all 9 discovery questions; return UserRequest."""
    root = (repo_root or Path.cwd()).resolve()
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  ParallelOps-Eval — Discovery (9 questions)              ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    print("── Repository ──")
    repo_path = _prompt("1. Which repository should be modified?", str(root))
    base_branch = _prompt("2. Which branch should be used as base?", "main")

    print("\n── Task ──")
    print("   Examples: fix bugs | add features | improve tests | update docs | refactor")
    task = _prompt("3. What changes do you want?")
    if not task:
        raise SystemExit("Task description is required.")
    max_lanes = int(_prompt("4. How many parallel lanes?", "3") or "3")

    print("\n── Execution ──")
    auto_generate = _yes_no("5. Should tasks be generated automatically?", True)
    auto_commit = _yes_no("6. Should commits happen automatically?", False)
    auto_push = _yes_no("7. Should branches be pushed automatically to GitHub?", True)
    require_merge_approval = _yes_no("8. Require approval before merging to main?", True)

    print("\n── Verification ──")
    verify = _verify_commands()
    if not verify:
        verify = ["npm run lint", "npm run build", "npm test"]

    req = UserRequest(
        repo_path=repo_path,
        base_branch=base_branch,
        task_description=task,
        max_parallel_lanes=max_lanes,
        auto_generate_tasks=auto_generate,
        auto_commit_lanes=auto_commit,
        auto_push_lanes=auto_push,
        require_merge_approval=require_merge_approval,
        verification_commands=verify,
        run_a2=False,
        approved=False,
    )

    out = Path(repo_path).resolve() / ".parallelops/artifacts/user_request.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    save_user_request_json(req, out)
    print(f"\n✅ Saved: {out}\n")
    return req
