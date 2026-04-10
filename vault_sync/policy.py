"""Policy enforcement for secret access — define which paths and keys are readable."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional


@dataclass
class PolicyRule:
    path_pattern: str
    allowed_keys: Optional[List[str]] = None  # None means all keys allowed
    deny: bool = False

    def matches_path(self, path: str) -> bool:
        return fnmatch(path.strip("/"), self.path_pattern.strip("/"))

    def allows_key(self, key: str) -> bool:
        if self.allowed_keys is None:
            return True
        return any(fnmatch(key.lower(), pattern.lower()) for pattern in self.allowed_keys)


@dataclass
class Policy:
    rules: List[PolicyRule] = field(default_factory=list)

    def is_path_allowed(self, path: str) -> bool:
        for rule in reversed(self.rules):
            if rule.matches_path(path):
                return not rule.deny
        return True

    def is_key_allowed(self, path: str, key: str) -> bool:
        for rule in reversed(self.rules):
            if rule.matches_path(path):
                if rule.deny:
                    return False
                return rule.allows_key(key)
        return True


def parse_policy(raw: List[dict]) -> Policy:
    """Parse a list of rule dicts into a Policy object."""
    rules = []
    for entry in raw:
        rules.append(PolicyRule(
            path_pattern=entry["path"],
            allowed_keys=entry.get("allowed_keys"),
            deny=entry.get("deny", False),
        ))
    return Policy(rules=rules)


def apply_policy(policy: Policy, path: str, secrets: dict) -> dict:
    """Filter secrets dict based on policy rules for a given path."""
    if not policy.is_path_allowed(path):
        return {}
    return {k: v for k, v in secrets.items() if policy.is_key_allowed(path, k)}
