"""Key aliasing support: map Vault secret keys to custom .env variable names."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class AliasMap:
    """Holds a mapping from original Vault key names to desired output names."""

    _aliases: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalise: both sides upper-cased, strip whitespace
        self._aliases = {
            k.strip().upper(): v.strip().upper()
            for k, v in self._aliases.items()
        }

    def resolve(self, key: str) -> str:
        """Return the aliased name for *key*, or *key* itself if no alias exists."""
        return self._aliases.get(key.upper(), key.upper())

    def has_alias(self, key: str) -> bool:
        """Return True when *key* has an explicit alias registered."""
        return key.upper() in self._aliases

    def all_aliases(self) -> Dict[str, str]:
        """Return a copy of the internal alias mapping."""
        return dict(self._aliases)

    def to_dict(self) -> Dict[str, str]:
        return self.all_aliases()


def load_alias_file(path: str | Path) -> AliasMap:
    """Load an alias map from a JSON file.

    The file must be a flat JSON object whose keys are original Vault key names
    and whose values are the desired output variable names, e.g.::

        {"db_password": "DATABASE_PASSWORD", "api_token": "SERVICE_API_KEY"}

    Raises:
        FileNotFoundError: if *path* does not exist.
        ValueError: if the file is not valid JSON or not a flat object.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Alias file not found: {path}")
    try:
        raw = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in alias file '{path}': {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Alias file must contain a JSON object, got {type(raw).__name__}")
    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError("Alias file keys and values must all be strings")
    return AliasMap(raw)


def apply_aliases(secrets: Dict[str, str], alias_map: AliasMap) -> Dict[str, str]:
    """Return a new dict with keys renamed according to *alias_map*."""
    return {alias_map.resolve(k): v for k, v in secrets.items()}
