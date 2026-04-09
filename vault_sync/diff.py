"""Utilities for computing and displaying secret diffs."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ChangeType(str, Enum):
    ADDED = "added"
    UPDATED = "updated"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass
class SecretChange:
    key: str
    change_type: ChangeType
    old_value: str | None = None
    new_value: str | None = None

    def __repr__(self) -> str:
        if self.change_type == ChangeType.ADDED:
            return f"[+] {self.key}"
        elif self.change_type == ChangeType.REMOVED:
            return f"[-] {self.key}"
        elif self.change_type == ChangeType.UPDATED:
            return f"[~] {self.key}"
        return f"[=] {self.key}"


def compute_diff(
    current: Dict[str, str],
    incoming: Dict[str, str],
) -> List[SecretChange]:
    """Compare current env state with incoming secrets and return a list of changes."""
    changes: List[SecretChange] = []

    all_keys = set(current) | set(incoming)

    for key in sorted(all_keys):
        if key in incoming and key not in current:
            changes.append(SecretChange(key=key, change_type=ChangeType.ADDED, new_value=incoming[key]))
        elif key in current and key not in incoming:
            changes.append(SecretChange(key=key, change_type=ChangeType.REMOVED, old_value=current[key]))
        elif current[key] != incoming[key]:
            changes.append(
                SecretChange(
                    key=key,
                    change_type=ChangeType.UPDATED,
                    old_value=current[key],
                    new_value=incoming[key],
                )
            )
        else:
            changes.append(SecretChange(key=key, change_type=ChangeType.UNCHANGED))

    return changes


def format_diff_summary(changes: List[SecretChange]) -> str:
    """Return a human-readable summary of the diff."""
    lines = []
    for change in changes:
        if change.change_type != ChangeType.UNCHANGED:
            lines.append(repr(change))
    if not lines:
        return "No changes detected."
    return "\n".join(lines)
