"""Checkpoint module: track and persist sync progress across runs."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CheckpointConfig:
    max_entries: int = 100
    ttl_seconds: float = 86400.0  # 24 hours

    def validate(self) -> None:
        if self.max_entries <= 0:
            raise ValueError("max_entries must be positive")
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")


@dataclass
class CheckpointEntry:
    path: str
    synced_at: float
    key_count: int
    checksum: str

    def is_expired(self, ttl_seconds: float) -> bool:
        return (time.time() - self.synced_at) > ttl_seconds

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "synced_at": self.synced_at,
            "key_count": self.key_count,
            "checksum": self.checksum,
        }

    @staticmethod
    def from_dict(data: dict) -> "CheckpointEntry":
        return CheckpointEntry(
            path=data["path"],
            synced_at=float(data["synced_at"]),
            key_count=int(data["key_count"]),
            checksum=data["checksum"],
        )


@dataclass
class Checkpoint:
    config: CheckpointConfig
    _entries: Dict[str, CheckpointEntry] = field(default_factory=dict)

    def record(self, path: str, key_count: int, checksum: str) -> CheckpointEntry:
        entry = CheckpointEntry(
            path=path,
            synced_at=time.time(),
            key_count=key_count,
            checksum=checksum,
        )
        self._entries[path] = entry
        self._evict()
        return entry

    def get(self, path: str) -> Optional[CheckpointEntry]:
        entry = self._entries.get(path)
        if entry is None:
            return None
        if entry.is_expired(self.config.ttl_seconds):
            del self._entries[path]
            return None
        return entry

    def all_paths(self) -> List[str]:
        return list(self._entries.keys())

    def _evict(self) -> None:
        if len(self._entries) <= self.config.max_entries:
            return
        sorted_paths = sorted(
            self._entries, key=lambda p: self._entries[p].synced_at
        )
        for path in sorted_paths[: len(self._entries) - self.config.max_entries]:
            del self._entries[path]

    def save(self, filepath: Path) -> None:
        data = {p: e.to_dict() for p, e in self._entries.items()}
        filepath.write_text(json.dumps(data, indent=2))

    def load(self, filepath: Path) -> None:
        if not filepath.exists():
            return
        raw = json.loads(filepath.read_text())
        self._entries = {p: CheckpointEntry.from_dict(v) for p, v in raw.items()}
