"""Throttle configuration and enforcement for Vault API calls."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Any

T = TypeVar("T")


@dataclass
class ThrottleConfig:
    """Configuration for request throttling."""
    min_interval: float = 0.1  # seconds between calls
    max_burst: int = 5         # allowed burst before throttling kicks in

    def validate(self) -> None:
        if self.min_interval <= 0:
            raise ValueError("min_interval must be positive")
        if self.max_burst < 1:
            raise ValueError("max_burst must be at least 1")


@dataclass
class ThrottleState:
    """Mutable state tracked per throttle instance."""
    _last_call: float = field(default=0.0, repr=False)
    _burst_count: int = field(default=0, repr=False)
    total_calls: int = 0
    total_delayed: int = 0

    def record_call(self, delayed: bool) -> None:
        self.total_calls += 1
        if delayed:
            self.total_delayed += 1


class Throttle:
    """Enforces a minimum interval between calls with burst allowance."""

    def __init__(self, config: ThrottleConfig) -> None:
        config.validate()
        self._config = config
        self._state = ThrottleState()

    @property
    def state(self) -> ThrottleState:
        return self._state

    def acquire(self) -> bool:
        """Block until the throttle allows the next call.

        Returns True if the call was delayed, False if it proceeded immediately.
        """
        now = time.monotonic()
        elapsed = now - self._state._last_call

        delayed = False
        if self._state._burst_count < self._config.max_burst:
            self._state._burst_count += 1
        else:
            if elapsed < self._config.min_interval:
                wait = self._config.min_interval - elapsed
                time.sleep(wait)
                delayed = True
            self._state._burst_count = 0

        self._state._last_call = time.monotonic()
        self._state.record_call(delayed)
        return delayed

    def wrap(self, fn: Callable[..., T]) -> Callable[..., T]:
        """Return a wrapped version of *fn* that respects this throttle."""
        def _inner(*args: Any, **kwargs: Any) -> T:
            self.acquire()
            return fn(*args, **kwargs)
        return _inner


def build_throttle(min_interval: float = 0.1, max_burst: int = 5) -> Throttle:
    """Convenience factory for a Throttle."""
    return Throttle(ThrottleConfig(min_interval=min_interval, max_burst=max_burst))
