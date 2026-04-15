"""High-watermark tracking for secret sync progress."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class WatermarkConfig:
    max_entries: int = 500

    def validate(self) -> None:
        if self.max_entries <= 0:
            raise ValueError("max_entries must be positive")


@dataclass
class WatermarkEntry:
    path: str
    key_count: int
    synced_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"path": self.path, "key_count": self.key_count, "synced_at": self.synced_at}

    @classmethod
    def from_dict(cls, data: dict) -> "WatermarkEntry":
        return cls(
            path=data["path"],
            key_count=data["key_count"],
            synced_at=data["synced_at"],
        )


@dataclass
class Watermark:
    config: WatermarkConfig = field(default_factory=WatermarkConfig)
    _entries: list = field(default_factory=list, init=False, repr=False)

    def record(self, path: str, key_count: int) -> WatermarkEntry:
        entry = WatermarkEntry(path=path, key_count=key_count)
        self._entries.append(entry)
        if len(self._entries) > self.config.max_entries:
            self._entries = self._entries[-self.config.max_entries :]
        return entry

    def latest(self, path: str) -> Optional[WatermarkEntry]:
        for entry in reversed(self._entries):
            if entry.path == path:
                return entry
        return None

    def peak(self, path: str) -> Optional[WatermarkEntry]:
        matches = [e for e in self._entries if e.path == path]
        if not matches:
            return None
        return max(matches, key=lambda e: e.key_count)

    def all_paths(self) -> list:
        seen: dict = {}
        for entry in self._entries:
            seen[entry.path] = entry
        return list(seen.keys())

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def load(self, path: Path) -> None:
        if not path.exists():
            return
        data = json.loads(path.read_text())
        self._entries = [WatermarkEntry.from_dict(d) for d in data]
