"""Load policy configuration from YAML or JSON files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from vault_sync.policy import Policy, parse_policy


def load_policy_file(path: str) -> Policy:
    """Load a policy from a YAML or JSON file.

    The file must contain a top-level list of rule objects.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    suffix = p.suffix.lower()
    text = p.read_text(encoding="utf-8")

    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
            raw = yaml.safe_load(text)
        except ImportError as exc:
            raise ImportError("PyYAML is required to load YAML policy files.") from exc
    elif suffix == ".json":
        raw = json.loads(text)
    else:
        raise ValueError(f"Unsupported policy file format: {suffix}")

    if not isinstance(raw, list):
        raise ValueError("Policy file must contain a top-level list of rules.")

    return parse_policy(raw)


def load_policy_or_default(path: Optional[str]) -> Policy:
    """Return loaded policy if path given, else an empty (allow-all) policy."""
    if path is None:
        return Policy()
    return load_policy_file(path)
