"""Load SecretSchema definitions from YAML or JSON files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from vault_sync.schema import FieldSchema, FieldType, SecretSchema


def _parse_field(raw: Dict[str, Any]) -> FieldSchema:
    name = raw["name"]
    ftype = FieldType(raw.get("type", "string"))
    required = bool(raw.get("required", True))
    pattern = raw.get("pattern")
    return FieldSchema(name=name, type=ftype, required=required, pattern=pattern)


def load_schema_file(path: str) -> SecretSchema:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    suffix = p.suffix.lower()
    if suffix == ".json":
        data = json.loads(p.read_text())
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError:  # pragma: no cover
            raise ImportError("PyYAML is required to load YAML schema files")
        data = yaml.safe_load(p.read_text())
    else:
        raise ValueError(f"Unsupported schema format: {suffix}")
    fields = [_parse_field(f) for f in data.get("fields", [])]
    return SecretSchema(fields=fields)


def load_schema_or_default(path: str | None) -> SecretSchema:
    """Return a loaded schema or an empty permissive schema if path is None."""
    if path is None:
        return SecretSchema()
    return load_schema_file(path)
