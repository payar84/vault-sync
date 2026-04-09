"""Backup and restore support for .env files before syncing."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class BackupMeta:
    original: Path
    backup: Path
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "original": str(self.original),
            "backup": str(self.backup),
            "created_at": self.created_at,
        }


def create_backup(env_path: Path, backup_dir: Path | None = None) -> BackupMeta | None:
    """Copy env_path to a timestamped backup file.

    Returns a BackupMeta instance, or None if the source file does not exist.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        return None

    if backup_dir is None:
        backup_dir = env_path.parent / ".vault_sync_backups"

    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    backup_name = f"{env_path.name}.{timestamp}.bak"
    backup_path = backup_dir / backup_name

    shutil.copy2(env_path, backup_path)
    return BackupMeta(original=env_path, backup=backup_path)


def restore_backup(meta: BackupMeta) -> None:
    """Restore a previously created backup to its original location."""
    backup = Path(meta.backup)
    if not backup.exists():
        raise FileNotFoundError(f"Backup file not found: {backup}")
    shutil.copy2(backup, meta.original)


def list_backups(env_path: Path, backup_dir: Path | None = None) -> list[Path]:
    """Return sorted list of backup files for the given env file."""
    env_path = Path(env_path)
    if backup_dir is None:
        backup_dir = env_path.parent / ".vault_sync_backups"

    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        return []

    pattern = f"{env_path.name}.*.bak"
    return sorted(backup_dir.glob(pattern))
