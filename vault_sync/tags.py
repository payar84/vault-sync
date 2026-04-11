"""Tag-based filtering and grouping of secrets by metadata tags."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class TagSet:
    """A collection of key-value tags attached to a secret path."""
    tags: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tags = {k.lower().strip(): v.strip() for k, v in self.tags.items()}

    def has(self, key: str, value: Optional[str] = None) -> bool:
        """Return True if the tag key exists, optionally matching value."""
        key = key.lower().strip()
        if key not in self.tags:
            return False
        if value is None:
            return True
        return self.tags[key] == value.strip()

    def keys(self) -> Set[str]:
        return set(self.tags.keys())

    def to_dict(self) -> Dict[str, str]:
        return dict(self.tags)


def parse_tags(raw: str) -> TagSet:
    """Parse a comma-separated 'key=value' string into a TagSet.

    Example: 'env=prod,team=backend' -> TagSet({'env': 'prod', 'team': 'backend'})
    """
    tags: Dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid tag format (expected key=value): '{part}'")
        k, _, v = part.partition("=")
        if not k.strip():
            raise ValueError(f"Tag key must not be empty in: '{part}'")
        tags[k.strip()] = v.strip()
    return TagSet(tags)


def filter_by_tags(
    secrets: Dict[str, TagSet],
    required: TagSet,
) -> List[str]:
    """Return paths whose TagSet satisfies ALL required tags."""
    matched: List[str] = []
    for path, tag_set in secrets.items():
        if all(tag_set.has(k, v) for k, v in required.tags.items()):
            matched.append(path)
    return sorted(matched)


def group_by_tag(secrets: Dict[str, TagSet], key: str) -> Dict[str, List[str]]:
    """Group secret paths by the value of a specific tag key."""
    groups: Dict[str, List[str]] = {}
    for path, tag_set in secrets.items():
        value = tag_set.tags.get(key.lower().strip(), "__untagged__")
        groups.setdefault(value, []).append(path)
    for group in groups.values():
        group.sort()
    return groups
