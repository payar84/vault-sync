"""Export secrets to different output formats (JSON, YAML, dotenv)."""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


class ExportFormat(str, Enum):
    DOTENV = "dotenv"
    JSON = "json"
    YAML = "yaml"


def _to_dotenv(secrets: Dict[str, str]) -> str:
    lines = []
    for key in sorted(secrets):
        value = secrets[key]
        if any(c in value for c in (" ", "\t", "#", "'", '"')):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n" if lines else ""


def _to_json(secrets: Dict[str, str], indent: int = 2) -> str:
    return json.dumps(dict(sorted(secrets.items())), indent=indent) + "\n"


def _to_yaml(secrets: Dict[str, str]) -> str:
    lines = []
    for key in sorted(secrets):
        value = secrets[key]
        needs_quotes = any(c in value for c in (":", "#", "{", "}", "[", "]", ",", "&", "*"))
        if needs_quotes:
            value = f'"{value}"'
        lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n" if lines else ""


def export_secrets(
    secrets: Dict[str, str],
    fmt: ExportFormat,
    output_path: Optional[Path] = None,
) -> str:
    """Serialize secrets to the requested format and optionally write to file."""
    if fmt == ExportFormat.DOTENV:
        content = _to_dotenv(secrets)
    elif fmt == ExportFormat.JSON:
        content = _to_json(secrets)
    elif fmt == ExportFormat.YAML:
        content = _to_yaml(secrets)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")

    if output_path is not None:
        output_path.write_text(content, encoding="utf-8")

    return content


def parse_export_format(value: str) -> ExportFormat:
    """Parse a string into an ExportFormat, raising ValueError on unknown values."""
    try:
        return ExportFormat(value.lower())
    except ValueError:
        valid = ", ".join(f.value for f in ExportFormat)
        raise ValueError(f"Unknown export format '{value}'. Valid options: {valid}")
