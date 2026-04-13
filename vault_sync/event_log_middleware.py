"""Middleware helpers to integrate EventLog with sync and auth flows."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from vault_sync.event_log import EventLog, EventType


def wrap_sync(sync_fn: Callable, log: EventLog) -> Callable:
    """Wrap a sync function so start/complete/fail events are recorded."""

    def _wrapped(*args, **kwargs):
        log.record(EventType.SYNC_STARTED, "sync started")
        try:
            result = sync_fn(*args, **kwargs)
            log.record(
                EventType.SYNC_COMPLETED,
                "sync completed",
                added=getattr(result, "added", 0),
                updated=getattr(result, "updated", 0),
                removed=getattr(result, "removed", 0),
            )
            return result
        except Exception as exc:
            log.record(EventType.SYNC_FAILED, str(exc))
            raise

    return _wrapped


def record_secret_read(log: EventLog, path: str, key: str) -> None:
    log.record(EventType.SECRET_READ, f"read {key} from {path}", path=path, key=key)


def record_secret_write(log: EventLog, key: str) -> None:
    log.record(EventType.SECRET_WRITE, f"wrote {key}", key=key)


def record_auth(log: EventLog, *, success: bool, detail: str = "") -> None:
    if success:
        log.record(EventType.AUTH_SUCCESS, detail or "authentication succeeded")
    else:
        log.record(EventType.AUTH_FAILURE, detail or "authentication failed")


def summarise(log: EventLog) -> Dict[str, int]:
    """Return a count of each event type recorded."""
    counts: Dict[str, int] = {}
    for evt in log.all_events():
        counts[evt.event_type.value] = counts.get(evt.event_type.value, 0) + 1
    return counts
