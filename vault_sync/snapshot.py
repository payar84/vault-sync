"""Snapshot support: capture and compare full secret state at a point in time."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Snapshot:
    timestamp: float
    secrets: Dict[str, str]
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "secrets": self.secrets,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            timestamp=data["timestamp"],
            secrets=data["secrets"],
            label=data.get("label"),
        )

    def diff(self, other: "Snapshot") -> Dict[str, tuple]:
        """Return changed keys between this snapshot and *other*.

        Returns a dict mapping key -> (old_value, new_value).  A value of
        None means the key was absent in that snapshot.
        """
        changes: Dict[str, tuple] = {}
        all_keys = set(self.secrets) | set(other.secrets)
        for key in all_keys:
            old = self.secrets.get(key)
            new = other.secrets.get(key)
            if old != new:
                changes[key] = (old, new)
        return changes


def save_snapshot(snapshot: Snapshot, directory: Path) -> Path:
    """Persist *snapshot* to *directory* as a JSON file."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"snapshot_{int(snapshot.timestamp)}.json"
    path = directory / filename
    path.write_text(json.dumps(snapshot.to_dict(), indent=2))
    return path


def load_snapshot(path: Path) -> Snapshot:
    """Load a snapshot from *path*."""
    data = json.loads(path.read_text())
    return Snapshot.from_dict(data)


def list_snapshots(directory: Path) -> List[Snapshot]:
    """Return all snapshots in *directory* sorted by timestamp (oldest first)."""
    if not directory.exists():
        return []
    paths = sorted(directory.glob("snapshot_*.json"))
    return [load_snapshot(p) for p in paths]


def take_snapshot(secrets: Dict[str, str], label: Optional[str] = None) -> Snapshot:
    """Create a new in-memory snapshot from *secrets*."""
    return Snapshot(timestamp=time.time(), secrets=dict(secrets), label=label)
