"""Debounce support for vault-sync: suppress rapid repeated sync triggers."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DebounceConfig:
    window_seconds: float = 2.0
    max_pending: int = 100

    def validate(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.max_pending <= 0:
            raise ValueError("max_pending must be positive")


@dataclass
class DebounceState:
    path: str
    first_seen: float = field(default_factory=time.monotonic)
    last_seen: float = field(default_factory=time.monotonic)
    count: int = 1

    def touch(self) -> None:
        self.last_seen = time.monotonic()
        self.count += 1

    def __repr__(self) -> str:
        return (
            f"DebounceState(path={self.path!r}, count={self.count}, "
            f"age={self.last_seen - self.first_seen:.3f}s)"
        )


class Debouncer:
    """Tracks pending paths and decides when they are ready to be processed."""

    def __init__(self, config: DebounceConfig) -> None:
        config.validate()
        self._config = config
        self._pending: Dict[str, DebounceState] = {}

    def push(self, path: str) -> bool:
        """Record a trigger for *path*.  Returns True if accepted, False if
        the pending queue is full."""
        if path in self._pending:
            self._pending[path].touch()
            return True
        if len(self._pending) >= self._config.max_pending:
            return False
        self._pending[path] = DebounceState(path=path)
        return True

    def ready(self, now: Optional[float] = None) -> list[str]:
        """Return paths whose debounce window has elapsed and remove them."""
        now = now if now is not None else time.monotonic()
        due = [
            p
            for p, s in self._pending.items()
            if (now - s.last_seen) >= self._config.window_seconds
        ]
        for p in due:
            del self._pending[p]
        return sorted(due)

    def pending_count(self) -> int:
        return len(self._pending)

    def clear(self) -> None:
        self._pending.clear()
