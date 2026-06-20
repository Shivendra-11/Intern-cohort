"""Git and worktree operations for A2 executor."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def text(self) -> str:
        out = self.stdout.strip()
        err = self.stderr.strip()
        if out and err:
            return f"{out}\n{err}"
        return out or err


@dataclass
class PushResult:
    branch: str
    ok: bool
    output: str
    github_url: str | None = None
    skipped: bool = False


def run_git(cwd: Path, *args: str, check: bool = False) -> CommandResult:
    cmd = ["git", *args]
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    result = CommandResult(cmd, proc.returncode, proc.stdout, proc.stderr)
    if check and not result.ok:
        raise RuntimeError(f"git failed: {' '.join(cmd)}\n{result.text()}")
    return result


def ensure_git_repo(repo_root: Path) -> None:
    if not (repo_root / ".git").exists():
        run_git(repo_root, "init", check=True)
    # Worktrees require at least one commit
    if run_git(repo_root, "rev-parse", "HEAD").returncode != 0:
        run_git(repo_root, "add", "-A", check=True)
        run_git(
            repo_root,
            "commit",
            "-m",
            "chore: parallelops initial commit",
            check=True,
        )


def create_worktree(
    repo_root: Path,
    worktree_path: Path,
    branch_name: str,
    base_branch: str = "main",
) -> CommandResult:
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    if worktree_path.exists():
        return run_git(repo_root, "worktree", "list")

    # Ensure base branch exists
    branches = run_git(repo_root, "branch", "--list", base_branch).stdout
    if base_branch not in branches and base_branch != "master":
        current = run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if current and current != "HEAD":
            run_git(repo_root, "branch", "-f", base_branch, check=True)

    branch_exists = branch_name in run_git(repo_root, "branch", "--list", branch_name).stdout
    if branch_exists:
        return run_git(
            repo_root,
            "worktree",
            "add",
            str(worktree_path),
            branch_name,
            check=True,
        )
    return run_git(
        repo_root,
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_path),
        base_branch if _branch_exists(repo_root, base_branch) else "HEAD",
        check=True,
    )


def _branch_exists(repo_root: Path, branch: str) -> bool:
    return branch in run_git(repo_root, "branch", "--list", branch).stdout


def remove_worktree(repo_root: Path, worktree_path: Path) -> CommandResult:
    if worktree_path.exists():
        return run_git(repo_root, "worktree", "remove", "--force", str(worktree_path))
    return CommandResult(["noop"], 0, "worktree already absent", "")


def merge_branch(repo_root: Path, branch_name: str, target: str = "main") -> CommandResult:
    run_git(repo_root, "checkout", target, check=True)
    return run_git(repo_root, "merge", "--no-ff", branch_name, "-m", f"merge({branch_name}): parallelops lane merge")


def list_conflicts(repo_root: Path) -> list[str]:
    result = run_git(repo_root, "diff", "--name-only", "--diff-filter=U")
    if not result.ok:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_changed_files(repo_root: Path, branch: str, base: str = "main") -> list[str]:
    result = run_git(repo_root, "diff", "--name-only", f"{base}...{branch}")
    return [l.strip() for l in result.stdout.splitlines() if l.strip()]


def has_remote(repo_root: Path, remote: str = "origin") -> bool:
    result = run_git(repo_root, "remote")
    return remote in result.stdout.split()


def push_branch(
    repo_root: Path, branch: str, remote: str = "origin", *, force_set_upstream: bool = True
) -> PushResult:
    """Push branch to remote; return GitHub tree URL when origin is github.com."""
    if not has_remote(repo_root, remote):
        return PushResult(
            branch=branch,
            ok=False,
            skipped=True,
            output=(
                f"no remote '{remote}' — add GitHub remote first:\n"
                f"  git remote add origin git@github.com:ORG/REPO.git"
            ),
            github_url=None,
        )
    if force_set_upstream:
        result = run_git(repo_root, "push", "-u", remote, branch)
    else:
        result = run_git(repo_root, "push", remote, branch)
    url = github_urls(repo_root, branch, remote).get("branch_url")
    return PushResult(
        branch=branch,
        ok=result.ok,
        output=result.text(),
        github_url=url,
        skipped=False,
    )


def push_plan_branches(
    repo_root: Path,
    branch_names: list[str],
    *,
    remote: str = "origin",
) -> list[PushResult]:
    """Push every lane branch to GitHub (visible under origin on github.com)."""
    return [push_branch(repo_root, b, remote) for b in branch_names]


def github_compare_url(repo_root: Path, base: str, head: str, remote: str = "origin") -> str | None:
    """URL to open a compare/PR view on GitHub."""
    urls = github_urls(repo_root, base, remote)
    web = urls.get("repo_url")
    if not web:
        return None
    return f"{web}/compare/{base}...{head}?expand=1"


def get_remote_url(repo_root: Path, remote: str = "origin") -> str | None:
    result = run_git(repo_root, "remote", "get-url", remote)
    if not result.ok:
        return None
    return result.stdout.strip()


def github_urls(repo_root: Path, branch: str, remote: str = "origin") -> dict[str, str | None]:
    """Return repo and branch tree URLs when origin is GitHub."""
    url = get_remote_url(repo_root, remote)
    if not url:
        return {"repo_url": None, "branch_url": None, "compare_url": None}
    web = _to_github_web(url)
    if not web:
        return {"repo_url": None, "branch_url": None, "compare_url": None}
    # Branch names like fix/navbar-bugs → /tree/fix/navbar-bugs
    branch_path = branch.strip("/")
    return {
        "repo_url": web,
        "branch_url": f"{web}/tree/{branch_path}",
        "compare_url": None,
    }


def _to_github_web(url: str) -> str | None:
    if url.startswith("git@"):
        # git@github.com:org/repo.git
        parts = url.replace(":", "/").replace("git@", "https://").split("/")
        if "github.com" not in parts:
            return None
        host_idx = parts.index("github.com")
        org = parts[host_idx + 1]
        repo = parts[host_idx + 2].removesuffix(".git")
        return f"https://github.com/{org}/{repo}"
    if "github.com" in url:
        return url.removesuffix(".git")
    return None
