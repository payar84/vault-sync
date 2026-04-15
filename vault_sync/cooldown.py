"""Cooldown tracking: prevents re-syncing a path too soon after a recent sync."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CooldownConfig:
    min_interval_seconds: float = 60.0
    max_tracked_paths: int = 1000

    def validate(self) -> None:
        if self.min_interval_seconds <= 0:
            raise ValueError("min_interval_seconds must be positive")
        if self.max_tracked_paths <= 0:
            raise ValueError("max_tracked_paths must be positive")


@dataclass
class CooldownStatus:
    path: str
    last_synced_at: Optional[float]
    ready: bool
    seconds_remaining: float

    def __repr__(self) -> str:
        state = "ready" if self.ready else f"cooling ({self.seconds_remaining:.1f}s left)"
        return f"CooldownStatus(path={self.path!r}, {state})"


@dataclass
class Cooldown:
    config: CooldownConfig
    _records: Dict[str, float] = field(default_factory=dict, init=False)

    def record(self, path: str, *, now: Optional[float] = None) -> None:
        """Mark a path as just synced."""
        if len(self._records) >= self.config.max_tracked_paths:
            # Evict the oldest entry
            oldest = min(self._records, key=lambda k: self._records[k])
            del self._records[oldest]
        self._records[path] = now if now is not None else time.monotonic()

    def check(self, path: str, *, now: Optional[float] = None) -> CooldownStatus:
        """Return the cooldown status for *path*."""
        ts = now if now is not None else time.monotonic()
        last = self._records.get(path)
        if last is None:
            return CooldownStatus(path=path, last_synced_at=None, ready=True, seconds_remaining=0.0)
        elapsed = ts - last
        remaining = max(0.0, self.config.min_interval_seconds - elapsed)
        return CooldownStatus(
            path=path,
            last_synced_at=last,
            ready=remaining == 0.0,
            seconds_remaining=remaining,
        )

    def is_ready(self, path: str, *, now: Optional[float] = None) -> bool:
        return self.check(path, now=now).ready

    def clear(self, path: str) -> bool:
        """Remove cooldown record for *path*. Returns True if it existed."""
        return self._records.pop(path, None) is not None

    def tracked_paths(self) -> list:
        return sorted(self._records.keys())
