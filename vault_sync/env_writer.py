"""Utilities for writing secrets to .env files."""

import os
from pathlib import Path
from typing import Dict


def _format_entry(key: str, value: str) -> str:
    """Format a single key=value line, quoting values that contain spaces."""
    if " " in value or "\t" in value:
        value = f'"{value}"'
    return f"{key}={value}\n"


def write_env_file(secrets: Dict[str, str], env_path: str, overwrite: bool = True) -> int:
    """
    Write *secrets* to *env_path*.

    If *overwrite* is False and the file already exists, existing keys are
    preserved and only new keys are appended.

    Returns the number of keys written.
    """
    path = Path(env_path)
    existing: Dict[str, str] = {}

    if not overwrite and path.exists():
        existing = read_env_file(env_path)

    merged = {**existing, **secrets} if overwrite else {**secrets, **existing}

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for key, value in sorted(merged.items()):
            fh.write(_format_entry(key, value))

    return len(secrets)


def read_env_file(env_path: str) -> Dict[str, str]:
    """Parse an existing .env file and return a dict of key/value pairs."""
    result: Dict[str, str] = {}
    path = Path(env_path)
    if not path.exists():
        return result

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip().strip('"')
    return result


def delete_env_keys(keys: list, env_path: str) -> int:
    """
    Remove the specified *keys* from an existing .env file.

    Returns the number of keys actually removed.
    """
    existing = read_env_file(env_path)
    keys_to_remove = set(keys)
    removed = keys_to_remove & existing.keys()
    if not removed:
        return 0

    updated = {k: v for k, v in existing.items() if k not in keys_to_remove}
    path = Path(env_path)
    with path.open("w", encoding="utf-8") as fh:
        for key, value in sorted(updated.items()):
            fh.write(_format_entry(key, value))

    return len(removed)
