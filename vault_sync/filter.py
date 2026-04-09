"""Secret key filtering support for vault-sync."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FilterConfig:
    """Configuration for filtering secret keys."""

    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    prefix_filter: Optional[str] = None

    def __post_init__(self) -> None:
        self.prefix_filter = (
            self.prefix_filter.upper() if self.prefix_filter else None
        )

    def is_allowed(self, key: str) -> bool:
        """Return True if *key* passes all active filter rules."""
        upper = key.upper()

        if self.prefix_filter and not upper.startswith(self.prefix_filter):
            return False

        if self.exclude_patterns and any(
            fnmatch.fnmatch(upper, p.upper()) for p in self.exclude_patterns
        ):
            return False

        if self.include_patterns and not any(
            fnmatch.fnmatch(upper, p.upper()) for p in self.include_patterns
        ):
            return False

        return True


def apply_filter(secrets: dict, config: FilterConfig) -> dict:
    """Return a new dict containing only keys allowed by *config*."""
    return {k: v for k, v in secrets.items() if config.is_allowed(k)}


def parse_patterns(raw: str) -> List[str]:
    """Split a comma-separated pattern string into a list of patterns."""
    return [p.strip() for p in re.split(r"[,\s]+", raw.strip()) if p.strip()]
