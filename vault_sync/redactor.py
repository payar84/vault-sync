"""Redactor module: masks sensitive secret values in output and logs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

# Patterns whose values should always be redacted
DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api_key|apikey|private_key|auth)",
]

REDACTED_PLACEHOLDER = "***REDACTED***"


@dataclass
class Redactor:
    """Redacts sensitive values from a dict of secrets before display or logging."""

    patterns: List[str] = field(default_factory=lambda: list(DEFAULT_SENSITIVE_PATTERNS))
    placeholder: str = REDACTED_PLACEHOLDER

    def __post_init__(self) -> None:
        self._compiled = [re.compile(p) for p in self.patterns]

    def is_sensitive(self, key: str) -> bool:
        """Return True if the key matches any sensitive pattern."""
        return any(rx.search(key) for rx in self._compiled)

    def redact(self, secrets: Dict[str, str]) -> Dict[str, str]:
        """Return a copy of secrets with sensitive values replaced."""
        return {
            k: (self.placeholder if self.is_sensitive(k) else v)
            for k, v in secrets.items()
        }

    def redact_value(self, key: str, value: str) -> str:
        """Redact a single value based on its key."""
        return self.placeholder if self.is_sensitive(key) else value


def build_redactor(extra_patterns: List[str] | None = None) -> Redactor:
    """Create a Redactor with default patterns plus any extras."""
    patterns = list(DEFAULT_SENSITIVE_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)
    return Redactor(patterns=patterns)
