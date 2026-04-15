"""Ledger: tracks which secrets have been synced, when, and to which env file."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LedgerEntry:
    key: str
    path: str
    env_file: str
    synced_at: str
    checksum: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "path": self.path,
            "env_file": self.env_file,
            "synced_at": self.synced_at,
            "checksum": self.checksum,
        }

    @staticmethod
    def from_dict(d: dict) -> "LedgerEntry":
        return LedgerEntry(
            key=d["key"],
            path=d["path"],
            env_file=d["env_file"],
            synced_at=d["synced_at"],
            checksum=d.get("checksum"),
        )


@dataclass
class Ledger:
    _entries: Dict[str, LedgerEntry] = field(default_factory=dict)

    def record(self, key: str, path: str, env_file: str, checksum: Optional[str] = None) -> LedgerEntry:
        entry = LedgerEntry(
            key=key,
            path=path,
            env_file=env_file,
            synced_at=datetime.now(timezone.utc).isoformat(),
            checksum=checksum,
        )
        self._entries[key] = entry
        return entry

    def get(self, key: str) -> Optional[LedgerEntry]:
        return self._entries.get(key)

    def all_entries(self) -> List[LedgerEntry]:
        return sorted(self._entries.values(), key=lambda e: e.key)

    def remove(self, key: str) -> bool:
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in self.all_entries()]
        path.write_text(json.dumps(data, indent=2))

    @staticmethod
    def load(path: Path) -> "Ledger":
        ledger = Ledger()
        if not path.exists():
            return ledger
        data = json.loads(path.read_text())
        for item in data:
            entry = LedgerEntry.from_dict(item)
            ledger._entries[entry.key] = entry
        return ledger
