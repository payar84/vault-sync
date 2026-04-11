"""Lint .env files for common issues such as duplicate keys, empty values, and invalid key names."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from vault_sync.env_writer import read_env_file

_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def __repr__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    path: Path
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def __repr__(self) -> str:
        return (
            f"LintResult({self.path}, errors={self.error_count}, "
            f"warnings={self.warning_count})"
        )


def lint_env_file(path: Path) -> LintResult:
    """Run all lint checks against a .env file and return a LintResult."""
    result = LintResult(path=path)

    if not path.exists():
        result.issues.append(LintIssue(key="<file>", message="File does not exist", severity="error"))
        return result

    data = read_env_file(path)
    seen: dict[str, int] = {}

    for key, value in data.items():
        seen[key] = seen.get(key, 0) + 1

        if not _VALID_KEY_RE.match(key):
            result.issues.append(LintIssue(
                key=key,
                message="Key contains invalid characters or does not follow UPPER_SNAKE_CASE",
                severity="error",
            ))

        if value.strip() == "":
            result.issues.append(LintIssue(
                key=key,
                message="Value is empty or whitespace-only",
                severity="warning",
            ))

    for key, count in seen.items():
        if count > 1:
            result.issues.append(LintIssue(
                key=key,
                message=f"Duplicate key appears {count} times",
                severity="error",
            ))

    return result
