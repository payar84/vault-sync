"""Attach and query labels on secret paths for organisational metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelSet:
    """A collection of string labels attached to a vault path."""

    path: str
    labels: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.path = self.path.strip("/")
        self.labels = [lbl.strip().lower() for lbl in self.labels if lbl.strip()]

    def has(self, label: str) -> bool:
        """Return True if *label* (case-insensitive) is present."""
        return label.strip().lower() in self.labels

    def add(self, label: str) -> None:
        """Add *label* if not already present."""
        normalised = label.strip().lower()
        if normalised and normalised not in self.labels:
            self.labels.append(normalised)

    def remove(self, label: str) -> bool:
        """Remove *label*; return True if it was present."""
        normalised = label.strip().lower()
        if normalised in self.labels:
            self.labels.remove(normalised)
            return True
        return False

    def to_dict(self) -> Dict[str, object]:
        return {"path": self.path, "labels": sorted(self.labels)}


@dataclass
class LabelRegistry:
    """Registry mapping paths to their LabelSets."""

    _store: Dict[str, LabelSet] = field(default_factory=dict, repr=False)

    def register(self, path: str, labels: Optional[List[str]] = None) -> LabelSet:
        """Create or replace the LabelSet for *path*."""
        ls = LabelSet(path=path, labels=list(labels or []))
        self._store[ls.path] = ls
        return ls

    def get(self, path: str) -> Optional[LabelSet]:
        """Return the LabelSet for *path*, or None."""
        return self._store.get(path.strip("/"))

    def find_by_label(self, label: str) -> List[LabelSet]:
        """Return all LabelSets that carry *label*."""
        return [ls for ls in self._store.values() if ls.has(label)]

    def all_labels(self) -> List[str]:
        """Return a sorted, deduplicated list of every label in the registry."""
        seen: set[str] = set()
        for ls in self._store.values():
            seen.update(ls.labels)
        return sorted(seen)

    def to_dict(self) -> Dict[str, object]:
        return {path: ls.to_dict() for path, ls in sorted(self._store.items())}
