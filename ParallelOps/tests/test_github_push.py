"""Tests for GitHub push helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from parallelops import git_ops


class TestGitHubPush(unittest.TestCase):
    def test_branch_url_with_slashes(self) -> None:
        url = git_ops._to_github_web("git@github.com:acme/my-repo.git")
        self.assertEqual(url, "https://github.com/acme/my-repo")
        # no remote in /tmp — repo_url None; test path building via compare
        compare = git_ops.github_compare_url(Path("/tmp"), "main", "fix/navbar-bugs")
        self.assertIsNone(compare)

    def test_push_without_remote_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git_ops.run_git(root, "init")
            git_ops.run_git(root, "commit", "--allow-empty", "-m", "init")
            git_ops.run_git(root, "branch", "-M", "main")
            result = git_ops.push_branch(root, "main")
            self.assertFalse(result.ok)
            self.assertTrue(result.skipped)
            self.assertIn("no remote", result.output.lower())


if __name__ == "__main__":
    unittest.main()
