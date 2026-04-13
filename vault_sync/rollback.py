from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from vault_sync.backup import BackupMeta, create_backup, list_backups, restore_backup


@dataclass
class RollbackResult:
    success: bool
    backup_used: Optional[BackupMeta] = None
    message: str = ""

    @staticmethod
    def ok(meta: BackupMeta) -> "RollbackResult":
        return RollbackResult(success=True, backup_used=meta, message=f"Rolled back to {meta.timestamp}")

    @staticmethod
    def fail(reason: str) -> "RollbackResult":
        return RollbackResult(success=False, message=reason)

    def __repr__(self) -> str:
        status = "ok" if self.success else "fail"
        return f"RollbackResult({status}, {self.message!r})"


def rollback_to_latest(env_path: Path, backup_dir: Path) -> RollbackResult:
    """Restore the most recent backup of the given env file."""
    backups = list_backups(backup_dir, env_path)
    if not backups:
        return RollbackResult.fail("No backups found")
    latest = backups[0]
    restored = restore_backup(latest, env_path)
    if not restored:
        return RollbackResult.fail(f"Backup file missing: {latest.backup_path}")
    return RollbackResult.ok(latest)


def rollback_to_timestamp(env_path: Path, backup_dir: Path, timestamp: str) -> RollbackResult:
    """Restore the backup closest to the given ISO timestamp string."""
    backups = list_backups(backup_dir, env_path)
    if not backups:
        return RollbackResult.fail("No backups found")
    match = next((b for b in backups if b.timestamp.startswith(timestamp)), None)
    if match is None:
        return RollbackResult.fail(f"No backup matching timestamp prefix: {timestamp!r}")
    restored = restore_backup(match, env_path)
    if not restored:
        return RollbackResult.fail(f"Backup file missing: {match.backup_path}")
    return RollbackResult.ok(match)


def safe_sync_with_rollback(env_path: Path, backup_dir: Path, sync_fn) -> RollbackResult:
    """Create a backup, run sync_fn; roll back automatically on exception."""
    meta = create_backup(env_path, backup_dir)
    try:
        sync_fn()
        return RollbackResult(success=True, backup_used=meta, message="Sync succeeded")
    except Exception as exc:  # noqa: BLE001
        if meta is not None:
            restore_backup(meta, env_path)
            return RollbackResult.fail(f"Sync failed ({exc}); rolled back to {meta.timestamp}")
        return RollbackResult.fail(f"Sync failed ({exc}); no backup available")
