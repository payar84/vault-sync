"""Secret pinning — lock a secret's value to a specific version/hash."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass
class PinnedSecret:
    key: str
    path: str
    hash: str
    pinned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def matches(self, value: str) -> bool:
        """Return True if *value* matches the stored hash."""
        return _sha256(value) == self.hash

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "path": self.path,
            "hash": self.hash,
            "pinned_at": self.pinned_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PinnedSecret":
        return cls(
            key=data["key"],
            path=data["path"],
            hash=data["hash"],
            pinned_at=data["pinned_at"],
        )


class PinStore:
    """Persist and query pinned secrets from a JSON file."""

    def __init__(self, store_path: Path) -> None:
        self._path = store_path
        self._pins: Dict[str, PinnedSecret] = {}
        if store_path.exists():
            self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        raw = json.loads(self._path.read_text())
        self._pins = {k: PinnedSecret.from_dict(v) for k, v in raw.items()}

    def save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._pins.items()}, indent=2)
        )

    # ------------------------------------------------------------------
    def pin(self, key: str, path: str, value: str) -> PinnedSecret:
        """Pin *key* at *path* to the hash of *value*."""
        entry = PinnedSecret(key=key, path=path, hash=_sha256(value))
        self._pins[key] = entry
        return entry

    def get(self, key: str) -> Optional[PinnedSecret]:
        return self._pins.get(key)

    def remove(self, key: str) -> bool:
        if key in self._pins:
            del self._pins[key]
            return True
        return False

    def all_pins(self) -> Dict[str, PinnedSecret]:
        return dict(self._pins)

    def check(self, key: str, value: str) -> Optional[bool]:
        """Return True/False if pinned, None if not pinned."""
        entry = self.get(key)
        if entry is None:
            return None
        return entry.matches(value)
