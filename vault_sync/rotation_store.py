"""Persistent JSON store for rotation records."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from vault_sync.rotation import RotationTracker

_DATE_FMT = "%Y-%m-%dT%H:%M:%S"


class RotationStore:
    """Load and persist rotation timestamps to/from a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> Dict[str, datetime]:
        if not self.path.exists():
            return {}
        with self.path.open() as fh:
            raw: Dict[str, str] = json.load(fh)
        return {k: datetime.fromisoformat(v) for k, v in raw.items()}

    def save(self, records: Dict[str, datetime]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as fh:
            json.dump({k: v.isoformat() for k, v in records.items()}, fh, indent=2)

    def populate_tracker(self, tracker: RotationTracker) -> None:
        """Load records from disk into a RotationTracker instance."""
        for key, ts in self.load().items():
            tracker.record_rotation(key, ts)

    def flush_tracker(self, tracker: RotationTracker) -> None:
        """Persist all records from a RotationTracker to disk."""
        self.save(dict(tracker._records))

    def mark(self, key: str, when: Optional[datetime] = None) -> None:
        """Mark a single key as rotated and persist immediately."""
        records = self.load()
        records[key] = when or datetime.utcnow()
        self.save(records)

    def remove(self, key: str) -> bool:
        """Remove a key's rotation record. Returns True if the key existed."""
        records = self.load()
        existed = key in records
        if existed:
            del records[key]
            self.save(records)
        return existed

    def all_keys(self) -> list[str]:
        return list(self.load().keys())
