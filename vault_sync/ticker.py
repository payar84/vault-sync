from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class TickerConfig:
    interval_seconds: float
    max_ticks: Optional[int] = None

    def validate(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.max_ticks is not None and self.max_ticks <= 0:
            raise ValueError("max_ticks must be positive when set")


@dataclass
class TickEvent:
    tick: int
    fired_at: str

    def to_dict(self) -> dict:
        return {"tick": self.tick, "fired_at": self.fired_at}


@dataclass
class TickerState:
    config: TickerConfig
    _ticks: List[TickEvent] = field(default_factory=list)

    def tick(self) -> TickEvent:
        n = len(self._ticks) + 1
        event = TickEvent(tick=n, fired_at=datetime.now(timezone.utc).isoformat())
        self._ticks.append(event)
        return event

    @property
    def count(self) -> int:
        return len(self._ticks)

    def is_done(self) -> bool:
        if self.config.max_ticks is None:
            return False
        return self.count >= self.config.max_ticks

    def history(self) -> List[TickEvent]:
        return list(self._ticks)

    def last(self) -> Optional[TickEvent]:
        return self._ticks[-1] if self._ticks else None
