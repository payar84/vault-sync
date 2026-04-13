"""Pre/post sync hook support for vault-sync."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HookConfig:
    pre_sync: List[str] = field(default_factory=list)
    post_sync: List[str] = field(default_factory=list)
    timeout: int = 30

    def validate(self) -> None:
        if self.timeout <= 0:
            raise ValueError("timeout must be a positive integer")


@dataclass
class HookResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def __repr__(self) -> str:
        status = "ok" if self.ok else f"failed({self.returncode})"
        return f"HookResult(command={self.command!r}, status={status})"


def run_hook(command: str, timeout: int = 30) -> HookResult:
    """Run a single shell hook command and return its result."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return HookResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except subprocess.TimeoutExpired:
        return HookResult(command=command, returncode=-1, stdout="", stderr="timeout")


def run_hooks(commands: List[str], timeout: int = 30) -> List[HookResult]:
    """Run a list of hook commands in order, stopping on first failure."""
    results: List[HookResult] = []
    for cmd in commands:
        result = run_hook(cmd, timeout=timeout)
        results.append(result)
        if not result.ok:
            break
    return results


def all_ok(results: List[HookResult]) -> bool:
    """Return True if all hook results indicate success."""
    return all(r.ok for r in results)


def failed_hooks(results: List[HookResult]) -> List[HookResult]:
    """Return only the hook results that did not succeed.

    Useful for reporting or logging which hooks failed after a sync run.
    """
    return [r for r in results if not r.ok]
