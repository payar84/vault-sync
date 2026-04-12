"""Checksum utilities for detecting secret file drift."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


def _sha256_of_dict(data: Dict[str, str]) -> str:
    """Return a stable SHA-256 hex digest of a key/value mapping."""
    serialised = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialised.encode()).hexdigest()


def _sha256_of_file(path: Path) -> Optional[str]:
    """Return SHA-256 hex digest of a file, or None if the file is missing."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class ChecksumRecord:
    """Stores expected checksums for a set of secrets and the env file."""

    secrets_digest: str
    file_digest: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "secrets_digest": self.secrets_digest,
            "file_digest": self.file_digest,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChecksumRecord":
        return cls(
            secrets_digest=data["secrets_digest"],
            file_digest=data.get("file_digest"),
            extra=data.get("extra", {}),
        )


def compute_record(
    secrets: Dict[str, str],
    env_path: Optional[Path] = None,
) -> ChecksumRecord:
    """Build a ChecksumRecord from live secrets and an optional env file."""
    file_digest = _sha256_of_file(env_path) if env_path else None
    return ChecksumRecord(
        secrets_digest=_sha256_of_dict(secrets),
        file_digest=file_digest,
    )


def verify_record(
    record: ChecksumRecord,
    secrets: Dict[str, str],
    env_path: Optional[Path] = None,
) -> Dict[str, bool]:
    """Compare a stored record against current state.

    Returns a dict with keys ``secrets_match`` and ``file_match``.
    ``file_match`` is True when no env_path is provided (nothing to check).
    """
    secrets_match = _sha256_of_dict(secrets) == record.secrets_digest
    if env_path is not None:
        file_match = _sha256_of_file(env_path) == record.file_digest
    else:
        file_match = True
    return {"secrets_match": secrets_match, "file_match": file_match}
