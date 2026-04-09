"""Value transformation helpers for vault-sync."""
from __future__ import annotations

from typing import Callable, Dict, List

# A transformer is any callable that takes (key, value) and returns a new value.
Transformer = Callable[[str, str], str]


def strip_whitespace(key: str, value: str) -> str:  # noqa: ARG001
    """Remove leading/trailing whitespace from *value*."""
    return value.strip()


def to_uppercase_value(key: str, value: str) -> str:  # noqa: ARG001
    """Convert *value* to uppercase."""
    return value.upper()


def mask_sensitive(key: str, value: str) -> str:
    """Replace value with a masked placeholder for sensitive keys."""
    sensitive_keywords = ("PASSWORD", "SECRET", "TOKEN", "KEY", "PRIVATE")
    if any(kw in key.upper() for kw in sensitive_keywords):
        return "***"
    return value


def apply_transforms(secrets: Dict[str, str], transformers: List[Transformer]) -> Dict[str, str]:
    """Apply each transformer in order to every secret value."""
    result: Dict[str, str] = {}
    for key, value in secrets.items():
        for fn in transformers:
            value = fn(key, value)
        result[key] = value
    return result


DEFAULT_TRANSFORMERS: List[Transformer] = [strip_whitespace]
