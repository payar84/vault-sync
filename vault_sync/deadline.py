"""Deadline enforcement for time-bounded sync operations."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeadlineConfig:
    max_duration_seconds: float
    warn_at_fraction: float = 0.8

    def validate(self) -> None:
        if self.max_duration_seconds <= 0:
            raise ValueError("max_duration_seconds must be positive")
        if not (0 < self.warn_at_fraction < 1):
            raise ValueError("warn_at_fraction must be between 0 and 1 (exclusive)")


@dataclass
class DeadlineStatus:
    elapsed: float
    limit: float
    expired: bool
    warned: bool

    def __repr__(self) -> str:
        state = "EXPIRED" if self.expired else ("WARN" if self.warned else "OK")
        return f"<DeadlineStatus {state} elapsed={self.elapsed:.2f}s limit={self.limit:.2f}s>"

    @property
    def remaining(self) -> float:
        return max(0.0, self.limit - self.elapsed)


@dataclass
class Deadline:
    config: DeadlineConfig
    _start: float = field(default_factory=time.monotonic, init=False)

    def reset(self) -> None:
        self._start = time.monotonic()

    def elapsed(self) -> float:
        return time.monotonic() - self._start

    def is_expired(self) -> bool:
        return self.elapsed() >= self.config.max_duration_seconds

    def is_warned(self) -> bool:
        threshold = self.config.max_duration_seconds * self.config.warn_at_fraction
        return self.elapsed() >= threshold

    def status(self) -> DeadlineStatus:
        e = self.elapsed()
        return DeadlineStatus(
            elapsed=e,
            limit=self.config.max_duration_seconds,
            expired=e >= self.config.max_duration_seconds,
            warned=e >= self.config.max_duration_seconds * self.config.warn_at_fraction,
        )


def make_deadline(max_seconds: float, warn_at: float = 0.8) -> Deadline:
    cfg = DeadlineConfig(max_duration_seconds=max_seconds, warn_at_fraction=warn_at)
    cfg.validate()
    return Deadline(config=cfg)
