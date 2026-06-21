"""Safely execute shell commands with timeouts and guardrails."""
from __future__ import annotations

import os
import shlex
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Union

CommandInput = Union[str, Sequence[str]]

# Substrings that indicate dangerous command patterns (best-effort blocklist).
_BLOCKED_SUBSTRINGS = (
    "rm -rf /",
    "rm -rf ~",
    ":(){ :|:& };:",
    "mkfs.",
    "dd if=",
    "> /dev/sda",
    "curl | sh",
    "wget | sh",
    "| bash",
    "| sh",
)

# When using shell=True, only allow a conservative set of command prefixes.
_SHELL_ALLOW_PREFIXES = (
    "npm ",
    "npx ",
    "node ",
    "python",
    "python3",
    "pytest",
    "pip ",
    "pip3 ",
    "cargo ",
    "go ",
    "mvn ",
    "gradle ",
    "./gradlew ",
    "make ",
    "echo ",
)


@dataclass(frozen=True)
class ShellResult:
    """Outcome of a executed command."""

    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @property
    def combined_output(self) -> str:
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts).strip()

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "ok": self.ok,
        }


class ShellExecutor:
    """Run subprocess commands with cwd confinement and optional shell mode."""

    def __init__(
        self,
        default_timeout: int = 300,
        allow_shell: bool = True,
    ) -> None:
        self.default_timeout = default_timeout
        self.allow_shell = allow_shell

    def run(
        self,
        command: CommandInput,
        cwd: str | None = None,
        timeout: int | None = None,
        env: Mapping[str, str] | None = None,
        shell: bool = False,
    ) -> ShellResult:
        """Execute a command and capture stdout/stderr.

        Prefer argv lists (shell=False). String commands require shell=True and
        pass a conservative safety check.
        """
        timeout = timeout if timeout is not None else self.default_timeout
        display_cmd = self._display_command(command, shell)

        if isinstance(command, str):
            self._validate_shell_command(command)
            if not shell:
                command = shlex.split(command)
                shell = False
            elif not self.allow_shell:
                raise ValueError("shell execution disabled; pass argv list instead")
        else:
            shell = False

        if cwd:
            cwd = os.path.abspath(cwd)
            if not os.path.isdir(cwd):
                raise ValueError(f"cwd is not a directory: {cwd}")

        merged_env: dict[str, str] | None = None
        if env:
            merged_env = os.environ.copy()
            merged_env.update(dict(env))

        start = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                env=merged_env,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            exit_code = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = 124
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            stderr = (stderr + "\nCommand timed out.").strip()
        except FileNotFoundError as exc:
            exit_code = 127
            stdout = ""
            stderr = str(exc)
        except OSError as exc:
            exit_code = 1
            stdout = ""
            stderr = str(exc)

        duration_ms = int((time.monotonic() - start) * 1000)
        return ShellResult(
            command=display_cmd,
            exit_code=exit_code,
            stdout=stdout.strip(),
            stderr=stderr.strip(),
            duration_ms=duration_ms,
            timed_out=timed_out,
        )

    @staticmethod
    def _display_command(command: CommandInput, shell: bool) -> str:
        if isinstance(command, str):
            return command
        return " ".join(shlex.quote(str(part)) for part in command)

    @classmethod
    def _validate_shell_command(cls, command: str) -> None:
        low = command.strip().lower()
        for blocked in _BLOCKED_SUBSTRINGS:
            if blocked in low:
                raise ValueError(f"blocked command pattern: {blocked!r}")

        if not any(low.startswith(prefix.strip()) for prefix in _SHELL_ALLOW_PREFIXES):
            raise ValueError(
                "shell command not in allowlist; pass an argv list or use a permitted prefix "
                f"({', '.join(_SHELL_ALLOW_PREFIXES[:6])}…)"
            )
