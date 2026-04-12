from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NotifyConfig:
    """Configuration for post-sync notifications."""

    command: str
    args: List[str] = field(default_factory=list)
    timeout: int = 30
    on_success: bool = True
    on_failure: bool = True

    def validate(self) -> None:
        if not self.command.strip():
            raise ValueError("notify command must not be empty")
        if self.timeout <= 0:
            raise ValueError("notify timeout must be positive")


@dataclass
class NotifyResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    error: Optional[str] = None

    @staticmethod
    def ok(stdout: str = "", stderr: str = "") -> "NotifyResult":
        return NotifyResult(success=True, returncode=0, stdout=stdout, stderr=stderr)

    def __repr__(self) -> str:
        status = "ok" if self.success else "failed"
        return f"NotifyResult({status}, rc={self.returncode})"


def run_notify(config: NotifyConfig, env_vars: Optional[dict] = None) -> NotifyResult:
    """Run the notification command, optionally injecting env_vars."""
    import os

    config.validate()
    cmd = [config.command] + config.args
    merged_env = {**os.environ, **(env_vars or {})}

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout,
            env=merged_env,
        )
        return NotifyResult(
            success=result.returncode == 0,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except subprocess.TimeoutExpired:
        return NotifyResult(
            success=False,
            returncode=-1,
            stdout="",
            stderr="",
            error=f"command timed out after {config.timeout}s",
        )
    except FileNotFoundError:
        return NotifyResult(
            success=False,
            returncode=-1,
            stdout="",
            stderr="",
            error=f"command not found: {config.command}",
        )
