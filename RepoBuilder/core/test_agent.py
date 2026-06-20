"""B3 test agent — discover, execute, and report test results."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional

from core.json_writer import JsonWriter
from core.report_generator import ReportGenerator, ReportSection
from core.shell_executor import ShellExecutor, ShellResult
from core.test_discovery import TestDiscovery, TestFrameworkSetup
from core.test_interpreter import interpret_failures, parse_counts


@dataclass
class TestExecutionResult:
    __test__ = False  # production dataclass, not a pytest test class
    command: str = ""
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    timed_out: bool = False
    passed: Optional[int] = None
    failed: Optional[int] = None
    skipped: Optional[int] = None
    interpretation: str = ""
    status: str = "SKIPPED"  # SUCCESS | FAILED | SKIPPED

    def combined_log(self) -> str:
        lines = [
            f"$ {self.command}",
            f"exit_code: {self.exit_code}",
            "",
            "=== stdout ===",
            self.stdout or "(empty)",
            "",
            "=== stderr ===",
            self.stderr or "(empty)",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "interpretation": self.interpretation,
            "status": self.status,
        }


@dataclass
class TestAgentResult:
    __test__ = False  # production dataclass, not a pytest test class
    repo: str
    repo_name: str
    frameworks: List[TestFrameworkSetup] = field(default_factory=list)
    primary: Optional[TestFrameworkSetup] = None
    execution: TestExecutionResult = field(default_factory=TestExecutionResult)

    def to_tests_json(self) -> dict:
        return {
            "repo": self.repo,
            "repo_name": self.repo_name,
            "framework": self.primary.framework if self.primary else None,
            "config_file": self.primary.config_file if self.primary else None,
            "test_files": self.primary.test_files if self.primary else [],
            "commands": {
                "install": self.primary.install if self.primary else [],
                "run": self.primary.commands if self.primary else [],
            },
            "frameworks_detected": [f.to_dict() for f in self.frameworks],
            "execution": self.execution.to_dict(),
            "passed": self.execution.passed,
            "failed": self.execution.failed,
            "status": self.execution.status,
        }


class TestAgent:
    """Discover test setup, execute tests, write workspace/{repo_name}/B3_tests/."""

    __test__ = False  # production agent class, not a pytest test class

    def __init__(
        self,
        workspace_root: str = "workspace",
        executor: Optional[ShellExecutor] = None,
        discovery: Optional[TestDiscovery] = None,
        timeout: int = 600,
    ) -> None:
        self.workspace_root = workspace_root
        self.executor = executor or ShellExecutor(default_timeout=timeout)
        self.discovery = discovery or TestDiscovery()
        self.json_writer = JsonWriter()
        self.report_gen = ReportGenerator()
        self.timeout = timeout

    def run(
        self,
        repo_path: str,
        output_dir: Optional[str] = None,
        execute: bool = True,
        skip_install: bool = False,
    ) -> TestAgentResult:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"not a directory: {repo_path}")

        repo_name = self.repo_name(repo_path)
        out_dir = output_dir or os.path.join(
            self.workspace_root, repo_name, "B3_tests"
        )

        frameworks = self.discovery.discover(repo_path)
        primary = frameworks[0] if frameworks else None

        execution = TestExecutionResult()
        if execute and primary:
            execution = self.execute_tests(repo_path, primary, skip_install=skip_install)
        elif not primary:
            execution.interpretation = "No test framework detected in this repository."
            execution.status = "SKIPPED"
        else:
            execution.interpretation = "Test execution skipped (--no-run)."
            execution.status = "SKIPPED"

        result = TestAgentResult(
            repo=repo_path,
            repo_name=repo_name,
            frameworks=frameworks,
            primary=primary,
            execution=execution,
        )

        os.makedirs(out_dir, exist_ok=True)
        self.json_writer.write(os.path.join(out_dir, "tests.json"), result.to_tests_json())
        with open(os.path.join(out_dir, "test_output.log"), "w", encoding="utf-8") as fh:
            fh.write(execution.combined_log() if execute and primary else "(no test run)\n")
        with open(os.path.join(out_dir, "tests.md"), "w", encoding="utf-8") as fh:
            fh.write(self.render_markdown(result))

        return result

    @staticmethod
    def repo_name(repo_path: str) -> str:
        return os.path.basename(repo_path.rstrip(os.sep)) or "repository"

    def execute_tests(
        self,
        repo_path: str,
        setup: TestFrameworkSetup,
        skip_install: bool = False,
    ) -> TestExecutionResult:
        if not skip_install:
            for cmd in setup.install:
                self._run_shell(cmd, repo_path)

        command = setup.commands[0] if setup.commands else ""
        if not command:
            return TestExecutionResult(
                interpretation="No run command available.",
                status="SKIPPED",
            )

        result = self._run_shell(command, repo_path)
        combined = result.combined_output
        counts = parse_counts(setup.framework, combined)
        interpretation = interpret_failures(
            setup.framework,
            combined,
            result.exit_code,
            counts,
            result.timed_out,
        )

        status = "SUCCESS" if result.ok and (counts.failed in (None, 0)) else "FAILED"
        if result.exit_code == 0 and counts.failed is None and not result.timed_out:
            status = "SUCCESS"

        return TestExecutionResult(
            command=result.command,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=result.duration_ms,
            timed_out=result.timed_out,
            passed=counts.passed,
            failed=counts.failed,
            skipped=counts.skipped,
            interpretation=interpretation,
            status=status,
        )

    def _run_shell(self, command: str, cwd: str) -> ShellResult:
        # Strip inline comments from discovery install hints.
        command = command.split("#", 1)[0].strip()
        if not command:
            return ShellResult(command="", exit_code=0, stdout="", stderr="", duration_ms=0)
        try:
            return self.executor.run(command, cwd=cwd, timeout=self.timeout, shell=True)
        except ValueError as exc:
            return ShellResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr=str(exc),
                duration_ms=0,
            )


    def render_markdown(self, result: TestAgentResult) -> str:
        sections: List[ReportSection] = []

        if not result.frameworks:
            sections.append(
                ReportSection(title="Summary", body="No test framework detected.")
            )
        else:
            primary = result.primary
            assert primary is not None
            file_lines = "\n".join(f"- `{f}`" for f in primary.test_files[:30])
            if len(primary.test_files) > 30:
                file_lines += f"\n- … and {len(primary.test_files) - 30} more"

            sections.append(
                ReportSection(
                    title="Summary",
                    body=self.report_gen.key_values(
                        [
                            ("Framework", primary.framework),
                            ("Config file", primary.config_file or "N/A"),
                            ("Install", " && ".join(primary.install) or "N/A"),
                            ("Run command", primary.commands[0] if primary.commands else "N/A"),
                            ("Status", result.execution.status),
                            ("Passed", result.execution.passed if result.execution.passed is not None else "N/A"),
                            ("Failed", result.execution.failed if result.execution.failed is not None else "N/A"),
                            ("Exit code", result.execution.exit_code),
                        ]
                    ),
                )
            )
            sections.append(
                ReportSection(title="Test files", body=file_lines or "*(none)*")
            )
            sections.append(
                ReportSection(
                    title="Interpretation",
                    body=result.execution.interpretation or "N/A",
                )
            )

            if len(result.frameworks) > 1:
                rows = [
                    [f.framework, f.config_file or "", len(f.test_files)]
                    for f in result.frameworks
                ]
                sections.append(
                    ReportSection(
                        title="All detected frameworks",
                        body=self.report_gen.table(
                            ["Framework", "Config", "Test files"], rows
                        ),
                    )
                )

        return self.report_gen.generate(
            f"Tests — {result.repo_name}",
            sections,
            footer=self.report_gen.timestamp_footer("test_agent"),
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="B3 test discovery and execution agent")
    ap.add_argument("repo", help="path to repository")
    ap.add_argument("--workspace", default="workspace")
    ap.add_argument("--output-dir", help="override B3_tests output directory")
    ap.add_argument("--no-run", action="store_true", help="discovery only, do not execute")
    ap.add_argument("--skip-install", action="store_true", help="skip install commands")
    args = ap.parse_args(argv)

    try:
        result = TestAgent(workspace_root=args.workspace).run(
            args.repo,
            output_dir=args.output_dir,
            execute=not args.no_run,
            skip_install=args.skip_install,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = args.output_dir or os.path.join(
        args.workspace, result.repo_name, "B3_tests"
    )
    print("Test agent complete")
    print(f"  output    : {os.path.abspath(out)}")
    print(f"  framework : {result.primary.framework if result.primary else 'none'}")
    print(f"  status    : {result.execution.status}")
    if result.execution.passed is not None:
        print(f"  passed    : {result.execution.passed}")
    if result.execution.failed is not None:
        print(f"  failed    : {result.execution.failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
