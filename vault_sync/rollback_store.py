from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from vault_sync.backup import BackupMeta

_INDEX_FILENAME = ".rollback_index.json"


@dataclass
class RollbackIndex:
    """Persisted index of backup metadata for a given env file."""
    entries: List[BackupMeta]

    def latest(self) -> Optional[BackupMeta]:
        return self.entries[0] if self.entries else None

    def add(self, meta: BackupMeta) -> None:
        self.entries.insert(0, meta)

    def prune(self, keep: int = 10) -> None:
        """Keep only the most recent *keep* entries."""
        self.entries = self.entries[:keep]


def _index_path(backup_dir: Path) -> Path:
    return backup_dir / _INDEX_FILENAME


def load_index(backup_dir: Path) -> RollbackIndex:
    path = _index_path(backup_dir)
    if not path.exists():
        return RollbackIndex(entries=[])
    data = json.loads(path.read_text())
    entries = [
        BackupMeta(
            original_path=e["original_path"],
            backup_path=e["backup_path"],
            timestamp=e["timestamp"],
        )
        for e in data.get("entries", [])
    ]
    return RollbackIndex(entries=entries)


def save_index(backup_dir: Path, index: RollbackIndex) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    path = _index_path(backup_dir)
    data = {"entries": [asdict(e) for e in index.entries]}
    path.write_text(json.dumps(data, indent=2))


def register_backup(backup_dir: Path, meta: BackupMeta, keep: int = 10) -> None:
    """Add *meta* to the persistent index, pruning old entries."""
    index = load_index(backup_dir)
    index.add(meta)
    index.prune(keep)
    save_index(backup_dir, index)
