from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class HeartbeatConfig:
    interval_seconds: float = 30.0
    max_misses: int = 3
    label: str = "default"

    def validate(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.max_misses < 1:
            raise ValueError("max_misses must be at least 1")
        if not self.label.strip():
            raise ValueError("label must not be blank")


@dataclass
class HeartbeatStatus:
    label: str
    last_beat: Optional[datetime]
    miss_count: int
    alive: bool

    def __repr__(self) -> str:
        ts = self.last_beat.isoformat() if self.last_beat else "never"
        state = "alive" if self.alive else "dead"
        return f"<HeartbeatStatus label={self.label!r} state={state} misses={self.miss_count} last={ts}>"


@dataclass
class Heartbeat:
    config: HeartbeatConfig
    _last_beat: Optional[datetime] = field(default=None, init=False, repr=False)
    _miss_count: int = field(default=0, init=False, repr=False)

    def beat(self) -> None:
        self._last_beat = datetime.now(timezone.utc)
        self._miss_count = 0

    def miss(self) -> None:
        self._miss_count += 1

    def status(self) -> HeartbeatStatus:
        alive = self._miss_count < self.config.max_misses
        return HeartbeatStatus(
            label=self.config.label,
            last_beat=self._last_beat,
            miss_count=self._miss_count,
            alive=alive,
        )

    def is_alive(self) -> bool:
        return self.status().alive

    def reset(self) -> None:
        self._last_beat = None
        self._miss_count = 0
