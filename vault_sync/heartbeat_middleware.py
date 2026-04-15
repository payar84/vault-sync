from __future__ import annotations

from typing import Callable, Any, Optional
from vault_sync.heartbeat import Heartbeat, HeartbeatConfig


def wrap_with_heartbeat(
    fn: Callable[..., Any],
    heartbeat: Heartbeat,
    on_failure: Optional[Callable[[Exception], None]] = None,
) -> Callable[..., Any]:
    """Wrap a callable so that a heartbeat is recorded on success
    and a miss is recorded on exception."""

    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            result = fn(*args, **kwargs)
            heartbeat.beat()
            return result
        except Exception as exc:
            heartbeat.miss()
            if on_failure is not None:
                on_failure(exc)
            raise

    return _wrapped


def make_guarded_heartbeat(
    label: str,
    interval_seconds: float = 30.0,
    max_misses: int = 3,
) -> Heartbeat:
    """Convenience factory that validates config and returns a ready Heartbeat."""
    cfg = HeartbeatConfig(
        interval_seconds=interval_seconds,
        max_misses=max_misses,
        label=label,
    )
    cfg.validate()
    return Heartbeat(config=cfg)
