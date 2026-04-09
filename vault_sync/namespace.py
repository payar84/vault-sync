"""Namespace support for mapping Vault secret paths to env var prefixes."""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class Namespace:
    """Maps a Vault secret path to an optional env var prefix."""
    path: str
    prefix: Optional[str] = None
    strip_prefix: bool = False

    def __post_init__(self):
        self.path = self.path.strip("/")
        if self.prefix:
            self.prefix = self.prefix.upper().rstrip("_")

    def format_key(self, key: str) -> str:
        """Apply prefix to a key, returning the final env var name."""
        key = key.upper()
        if self.prefix:
            return f"{self.prefix}_{key}"
        return key

    def matches_path(self, vault_path: str) -> bool:
        """Check whether a given vault path matches this namespace."""
        return vault_path.strip("/") == self.path


def parse_namespaces(raw: list[dict]) -> list[Namespace]:
    """Parse a list of namespace config dicts into Namespace objects.

    Each dict should have:
      - path (required): Vault secret path
      - prefix (optional): env var prefix
      - strip_prefix (optional): bool
    """
    namespaces = []
    for entry in raw:
        if "path" not in entry:
            raise ValueError(f"Namespace entry missing 'path': {entry}")
        namespaces.append(
            Namespace(
                path=entry["path"],
                prefix=entry.get("prefix"),
                strip_prefix=entry.get("strip_prefix", False),
            )
        )
    return namespaces


def apply_namespace(secrets: dict[str, str], namespace: Namespace) -> dict[str, str]:
    """Return a new dict with keys transformed according to the namespace."""
    return {namespace.format_key(k): v for k, v in secrets.items()}
