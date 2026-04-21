"""Middleware that records a checkpoint entry after each successful sync."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Dict

from vault_sync.checkpoint import Checkpoint, CheckpointConfig


def _checksum_of_secrets(secrets: Dict[str, str]) -> str:
    """Return a stable SHA-256 hex digest of a secrets dict."""
    stable = json.dumps(secrets, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode()).hexdigest()


def wrap_with_checkpoint(
    sync_fn: Callable[[str], Dict[str, str]],
    checkpoint: Checkpoint,
    filepath: Path,
) -> Callable[[str], Dict[str, str]]:
    """Wrap *sync_fn* so that a checkpoint is recorded after each call.

    Parameters
    ----------
    sync_fn:
        A callable that accepts a Vault path and returns a dict of secrets.
    checkpoint:
        The :class:`Checkpoint` instance to update.
    filepath:
        Where the checkpoint state should be persisted.
    """

    def _wrapped(path: str) -> Dict[str, str]:
        secrets = sync_fn(path)
        checksum = _checksum_of_secrets(secrets)
        checkpoint.record(path, key_count=len(secrets), checksum=checksum)
        checkpoint.save(filepath)
        return secrets

    return _wrapped


def make_checkpoint(
    filepath: Path,
    max_entries: int = 100,
    ttl_seconds: float = 86400.0,
) -> Checkpoint:
    """Convenience factory: create, validate, and load a :class:`Checkpoint`."""
    cfg = CheckpointConfig(max_entries=max_entries, ttl_seconds=ttl_seconds)
    cfg.validate()
    cp = Checkpoint(config=cfg)
    cp.load(filepath)
    return cp
