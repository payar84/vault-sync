"""Token-bucket rate limiter for Vault API calls."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RateLimitConfig:
    max_calls: int = 10
    period_seconds: float = 1.0
    burst: int = 0  # extra calls allowed above max_calls in a single burst

    def validate(self) -> None:
        if self.max_calls <= 0:
            raise ValueError("max_calls must be greater than zero")
        if self.period_seconds <= 0:
            raise ValueError("period_seconds must be greater than zero")
        if self.burst < 0:
            raise ValueError("burst must be zero or positive")


@dataclass
class RateLimiter:
    config: RateLimitConfig
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self.config.validate()
        self._tokens = float(self.config.max_calls + self.config.burst)
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        rate = self.config.max_calls / self.config.period_seconds
        self._tokens = min(
            float(self.config.max_calls + self.config.burst),
            self._tokens + elapsed * rate,
        )
        self._last_refill = now

    def acquire(self, block: bool = True) -> bool:
        """Consume one token.  Returns True on success, False if not blocking
        and no token is available."""
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            if not block:
                return False
            # Calculate wait time and sleep outside the lock would cause a
            # race, so we sleep briefly inside and retry.
            wait = (1.0 - self._tokens) * self.config.period_seconds / self.config.max_calls
        time.sleep(wait)
        return self.acquire(block=True)

    @property
    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens


def make_rate_limiter(max_calls: int = 10, period_seconds: float = 1.0, burst: int = 0) -> RateLimiter:
    """Convenience factory."""
    cfg = RateLimitConfig(max_calls=max_calls, period_seconds=period_seconds, burst=burst)
    return RateLimiter(config=cfg)
