"""Gateway module: single entry-point that enforces rate-limiting,
circuit-breaking, and deadline constraints before forwarding a
secret-read request to an underlying VaultClient."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from vault_sync.rate_limiter import RateLimiter, RateLimitConfig
from vault_sync.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from vault_sync.deadline import DeadlineConfig, DeadlineStatus, remaining


@dataclass
class GatewayConfig:
    rate_limit: RateLimitConfig = field(default_factory=lambda: RateLimitConfig(max_calls=10, period=1.0, burst=2))
    circuit_breaker: CircuitBreakerConfig = field(
        default_factory=lambda: CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30, success_threshold=2)
    )
    deadline: DeadlineConfig = field(default_factory=lambda: DeadlineConfig(max_duration=30.0, warn_at=0.8))


@dataclass
class GatewayResult:
    value: Optional[Dict[str, str]]
    success: bool
    reason: str = ""

    @staticmethod
    def ok(value: Dict[str, str]) -> "GatewayResult":
        return GatewayResult(value=value, success=True)

    @staticmethod
    def fail(reason: str) -> "GatewayResult":
        return GatewayResult(value=None, success=False, reason=reason)

    def __repr__(self) -> str:  # pragma: no cover
        if self.success:
            return f"GatewayResult(ok, keys={list(self.value or {})})"
        return f"GatewayResult(fail, reason={self.reason!r})"


class Gateway:
    def __init__(self, config: GatewayConfig, client) -> None:
        self._config = config
        self._client = client
        self._limiter = RateLimiter(config.rate_limit)
        self._breaker = CircuitBreaker(config.circuit_breaker)
        self._deadline_cfg = config.deadline

    def read_secret(self, path: str) -> GatewayResult:
        # Deadline check
        status: DeadlineStatus = remaining(self._deadline_cfg)
        if not status.within_deadline:
            return GatewayResult.fail("deadline exceeded")

        # Circuit breaker check
        if self._breaker.state == CircuitState.OPEN:
            return GatewayResult.fail("circuit open")

        # Rate limiter check
        allowed, wait = self._limiter.acquire()
        if not allowed:
            return GatewayResult.fail(f"rate limited (retry after {wait:.2f}s)")

        try:
            data = self._client.read_secret(path)
            self._breaker.record_success()
            return GatewayResult.ok(data or {})
        except Exception as exc:  # noqa: BLE001
            self._breaker.record_failure()
            return GatewayResult.fail(str(exc))
