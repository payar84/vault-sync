"""Scope filtering: restrict secret sync to a subset of Vault paths."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional


@dataclass
class ScopeConfig:
    """Defines which Vault paths are in scope for a sync operation."""

    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.include = [p.strip("/") for p in self.include]
        self.exclude = [p.strip("/") for p in self.exclude]

    def is_in_scope(self, path: str) -> bool:
        """Return True if *path* should be included in the sync."""
        normalized = path.strip("/")

        if self.exclude and any(
            fnmatch(normalized, pat) for pat in self.exclude
        ):
            return False

        if not self.include:
            return True

        return any(fnmatch(normalized, pat) for pat in self.include)

    def filter_paths(self, paths: List[str]) -> List[str]:
        """Return only the paths that are in scope."""
        return [p for p in paths if self.is_in_scope(p)]


def parse_scope(
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> ScopeConfig:
    """Build a :class:`ScopeConfig` from optional include/exclude lists."""
    return ScopeConfig(
        include=list(include or []),
        exclude=list(exclude or []),
    )
