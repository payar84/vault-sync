"""High-level manager that ties snapshots into the sync workflow."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from vault_sync.snapshot import (
    Snapshot,
    list_snapshots,
    save_snapshot,
    take_snapshot,
)


DEFAULT_SNAPSHOT_DIR = Path(".vault_sync") / "snapshots"
_MAX_SNAPSHOTS = 10


class SnapshotManager:
    """Manages a rolling window of secret snapshots on disk."""

    def __init__(
        self,
        directory: Path = DEFAULT_SNAPSHOT_DIR,
        max_snapshots: int = _MAX_SNAPSHOTS,
    ) -> None:
        if max_snapshots < 1:
            raise ValueError("max_snapshots must be at least 1")
        self.directory = directory
        self.max_snapshots = max_snapshots

    def capture(self, secrets: Dict[str, str], label: Optional[str] = None) -> Snapshot:
        """Take a snapshot and persist it, pruning old ones if needed."""
        snapshot = take_snapshot(secrets, label=label)
        save_snapshot(snapshot, self.directory)
        self._prune()
        return snapshot

    def latest(self) -> Optional[Snapshot]:
        """Return the most recent snapshot, or None if none exist."""
        snapshots = list_snapshots(self.directory)
        return snapshots[-1] if snapshots else None

    def history(self) -> List[Snapshot]:
        """Return all snapshots sorted oldest-first."""
        return list_snapshots(self.directory)

    def diff_latest(self, secrets: Dict[str, str]) -> Optional[Dict[str, tuple]]:
        """Diff *secrets* against the latest snapshot.  Returns None if no baseline."""
        baseline = self.latest()
        if baseline is None:
            return None
        current = take_snapshot(secrets)
        return baseline.diff(current)

    def _prune(self) -> None:
        """Remove oldest snapshots when the rolling window is exceeded."""
        paths = sorted(self.directory.glob("snapshot_*.json"))
        excess = len(paths) - self.max_snapshots
        for path in paths[:excess]:
            path.unlink(missing_ok=True)
