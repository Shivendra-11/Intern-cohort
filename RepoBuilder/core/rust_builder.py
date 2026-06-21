"""Generate a runnable Rust log-counting CLI under workspace."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.json_writer import JsonWriter

PROJECT_FILES: dict[str, str] = {
    "Cargo.toml": textwrap.dedent("""\
        [package]
        name = "logcount"
        version = "0.1.0"
        edition = "2021"
        description = "Count INFO/WARN/ERROR lines in a log file"

        [dependencies]
        clap = { version = "4", features = ["derive"] }
    """),
    "src/lib.rs": textwrap.dedent("""\
        //! Core log-counting logic, separate from `main.rs` for unit/integration tests.

        use std::fs;
        use std::io;
        use std::path::Path;

        /// Tally of log lines by severity level.
        #[derive(Debug, Default, PartialEq, Eq)]
        pub struct Counts {
            pub info: usize,
            pub warn: usize,
            pub error: usize,
        }

        /// Count INFO / WARN / ERROR lines in a block of text.
        ///
        /// Each line is counted once by highest severity. Matching is case-insensitive;
        /// `WARN` also matches `WARNING`.
        pub fn count_levels(text: &str) -> Counts {
            let mut counts = Counts::default();
            for line in text.lines() {
                let upper = line.to_uppercase();
                if upper.contains("ERROR") {
                    counts.error += 1;
                } else if upper.contains("WARN") {
                    counts.warn += 1;
                } else if upper.contains("INFO") {
                    counts.info += 1;
                }
            }
            counts
        }

        /// Read a file and count log levels. Returns `io::Error` if unreadable — never panics.
        pub fn analyze_file<P: AsRef<Path>>(path: P) -> io::Result<Counts> {
            let text = fs::read_to_string(path)?;
            Ok(count_levels(&text))
        }

        #[cfg(test)]
        mod tests {
            use super::*;

            #[test]
            fn counts_each_level() {
                let text = "INFO starting\\nWARN low disk\\nERROR boom\\nINFO done\\n";
                let c = count_levels(text);
                assert_eq!(c, Counts { info: 2, warn: 1, error: 1 });
            }

            #[test]
            fn empty_input_is_all_zero() {
                assert_eq!(count_levels(""), Counts::default());
            }
        }
    """),
    "src/main.rs": textwrap.dedent("""\
        //! CLI entry point: count INFO/WARN/ERROR lines in a log file.

        use std::process::ExitCode;

        use clap::Parser;
        use logcount::analyze_file;

        #[derive(Parser)]
        #[command(name = "logcount", about = "Count INFO/WARN/ERROR lines in a log file")]
        struct Cli {
            /// Path to the log file to analyze
            file: String,
        }

        fn main() -> ExitCode {
            let cli = Cli::parse();
            match analyze_file(&cli.file) {
                Ok(counts) => {
                    println!("INFO:  {}", counts.info);
                    println!("WARN:  {}", counts.warn);
                    println!("ERROR: {}", counts.error);
                    ExitCode::SUCCESS
                }
                Err(err) => {
                    eprintln!("error: could not read '{}': {}", cli.file, err);
                    ExitCode::FAILURE
                }
            }
        }
    """),
    "tests/integration.rs": textwrap.dedent("""\
        //! Integration tests for the public library API.

        use std::io::Write;

        use logcount::{analyze_file, count_levels, Counts};

        #[test]
        fn counts_levels_in_text() {
            let text = "INFO ok\\nWARN careful\\nERROR bad\\nWARNING also\\n";
            assert_eq!(count_levels(text), Counts { info: 1, warn: 2, error: 1 });
        }

        #[test]
        fn highest_severity_wins_per_line() {
            let text = "ERROR and WARN on one line\\nplain line\\n";
            assert_eq!(count_levels(text), Counts { info: 0, warn: 0, error: 1 });
        }

        #[test]
        fn missing_file_returns_error_not_panic() {
            let result = analyze_file("/no/such/file/at/all.log");
            assert!(result.is_err());
        }

        #[test]
        fn reads_a_real_file() {
            let mut tmp = std::env::temp_dir();
            tmp.push("logcount_it_sample.log");
            let mut f = std::fs::File::create(&tmp).unwrap();
            writeln!(f, "INFO boot\\nERROR crash").unwrap();

            let counts = analyze_file(&tmp).unwrap();
            assert_eq!(counts, Counts { info: 1, warn: 0, error: 1 });

            let _ = std::fs::remove_file(&tmp);
        }
    """),
    "README.md": textwrap.dedent("""\
        # logcount (Rust CLI)

        Count `INFO` / `WARN` / `ERROR` lines in a log file.

        - Each line is counted once by highest severity (`ERROR` beats `WARN` beats `INFO`).
        - Case-insensitive; `WARN` matches `WARNING`.
        - Missing files print a friendly stderr message and exit non-zero — no panic.

        ## Build

        ```bash
        cargo build
        ```

        ## Run

        ```bash
        cargo run -- path/to/app.log
        ```

        Example output:

        ```
        INFO:  12
        WARN:  3
        ERROR: 1
        ```

        ## Test

        ```bash
        cargo test
        ```
    """),
}


@dataclass
class BuildProof:
    test_command: str = "cargo test"
    test_exit_code: int = 1
    test_stdout: str = ""
    test_stderr: str = ""
    smoke_command: str = ""
    smoke_exit_code: int = 1
    smoke_output: str = ""
    passed: int | None = None
    failed: int | None = None

    def to_dict(self) -> dict:
        return {
            "test_command": self.test_command,
            "test_exit_code": self.test_exit_code,
            "test_stdout": self.test_stdout,
            "test_stderr": self.test_stderr,
            "smoke_command": self.smoke_command,
            "smoke_exit_code": self.smoke_exit_code,
            "smoke_output": self.smoke_output,
            "passed": self.passed,
            "failed": self.failed,
        }


@dataclass
class RustBuildResult:
    repo_name: str
    project_path: str
    files: list[str] = field(default_factory=list)
    status: str = "FAILED"
    proof: BuildProof = field(default_factory=BuildProof)

    def to_status_json(self) -> dict:
        return {
            "project": "rust",
            "repo_name": self.repo_name,
            "project_path": self.project_path,
            "status": self.status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stack": {
                "language": "rust",
                "tooling": "cargo",
                "cli": "clap",
            },
            "cli": {
                "binary": "logcount",
                "usage": "logcount <file>",
                "counts": ["INFO", "WARN", "ERROR"],
            },
            "files": self.files,
            "proof": self.proof.to_dict(),
        }


class RustBuilder:
    """Scaffold Rust log-count CLI and prove with cargo test."""

    def __init__(self, workspace_root: str = "workspace") -> None:
        self.workspace_root = workspace_root
        self.json_writer = JsonWriter()

    def build(
        self,
        repo_path: str,
        *,
        run_proof: bool = True,
        output_dir: str | None = None,
    ) -> RustBuildResult:
        repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(repo_path):
            raise ValueError(f"not a directory: {repo_path}")

        repo_name = self.repo_name(repo_path)
        project_path = output_dir or os.path.join(
            self.workspace_root,
            repo_name,
            "generated_projects",
            "rust",
        )

        files = self._write_project(project_path)
        proof = BuildProof()
        status = "GENERATED"

        if run_proof:
            proof = self._prove(project_path)
            ok = proof.test_exit_code == 0 and proof.smoke_exit_code == 0
            status = "SUCCESS" if ok else "FAILED"

        result = RustBuildResult(
            repo_name=repo_name,
            project_path=os.path.abspath(project_path),
            files=files,
            status=status,
            proof=proof,
        )

        self.json_writer.write(
            os.path.join(project_path, "status.json"),
            result.to_status_json(),
        )
        return result

    @staticmethod
    def repo_name(repo_path: str) -> str:
        return os.path.basename(repo_path.rstrip(os.sep)) or "repository"

    def _write_project(self, project_path: str) -> list[str]:
        created: list[str] = []
        for rel, content in PROJECT_FILES.items():
            path = os.path.join(project_path, rel)
            os.makedirs(os.path.dirname(path) or project_path, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            created.append(os.path.abspath(path))
        return created

    def _cargo_env(self) -> dict:
        env = os.environ.copy()
        cargo_home = os.path.join(os.path.expanduser("~"), ".cargo", "bin")
        if os.path.isdir(cargo_home):
            env["PATH"] = cargo_home + os.pathsep + env.get("PATH", "")
        return env

    def _prove(self, project_path: str) -> BuildProof:
        proof = BuildProof()
        env = self._cargo_env()

        if not self._find_cargo(env):
            proof.test_stderr = "cargo not found on PATH"
            return proof

        proc = subprocess.run(
            ["cargo", "test", "--quiet"],
            cwd=project_path,
            capture_output=True,
            text=True,
            env=env,
        )
        proof.test_command = "cargo test --quiet"
        proof.test_exit_code = proc.returncode
        proof.test_stdout = (proc.stdout or "").strip()
        proof.test_stderr = (proc.stderr or "").strip()
        self._parse_cargo_counts(proof)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".log",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write("INFO boot\nWARN disk\nERROR halt\n")
            log_path = tmp.name

        try:
            run = subprocess.run(
                ["cargo", "run", "--quiet", "--", log_path],
                cwd=project_path,
                capture_output=True,
                text=True,
                env=env,
            )
            missing = subprocess.run(
                ["cargo", "run", "--quiet", "--", "/no/such/logcount_smoke.log"],
                cwd=project_path,
                capture_output=True,
                text=True,
                env=env,
            )
        finally:
            try:
                os.unlink(log_path)
            except OSError:
                pass

        proof.smoke_command = "cargo run (valid file + missing file)"
        proof.smoke_exit_code = 0 if run.returncode == 0 and missing.returncode != 0 else 1
        proof.smoke_output = "\n".join(
            part
            for part in [
                (run.stdout or "").strip(),
                (missing.stderr or "").strip(),
            ]
            if part
        )

        if proof.test_exit_code != 0:
            proof.smoke_exit_code = proof.smoke_exit_code or 1

        return proof

    @staticmethod
    def _parse_cargo_counts(proof: BuildProof) -> None:
        combined = proof.test_stdout + "\n" + proof.test_stderr
        passed = 0
        failed = 0
        for m in re.finditer(r"test result: ok\.\s*(\d+) passed;\s*(\d+) failed", combined):
            passed += int(m.group(1))
            failed += int(m.group(2))
        if passed or failed:
            proof.passed = passed
            proof.failed = failed


    @staticmethod
    def _find_cargo(env: dict | None = None) -> str | None:
        from shutil import which

        path = (env or os.environ).get("PATH")
        return which("cargo", path=path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate Rust logcount CLI project")
    ap.add_argument("repo", help="repository path (used for workspace repo_name)")
    ap.add_argument("--workspace", default="workspace")
    ap.add_argument("--output-dir", help="override project output directory")
    ap.add_argument("--no-proof", action="store_true", help="skip cargo test/smoke proof")
    args = ap.parse_args(argv)

    try:
        result = RustBuilder(workspace_root=args.workspace).build(
            args.repo,
            run_proof=not args.no_proof,
            output_dir=args.output_dir,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Rust project {result.status}")
    print(f"  path   : {result.project_path}")
    print(f"  status : {os.path.join(result.project_path, 'status.json')}")
    if result.proof.passed is not None:
        print(f"  tests  : {result.proof.passed} passed, {result.proof.failed or 0} failed")
    elif result.proof.test_stderr:
        print(f"  tests  : {result.proof.test_stderr[:200]}")
    if result.proof.smoke_output:
        print(f"  smoke  : {result.proof.smoke_output.splitlines()[0]}")
    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
