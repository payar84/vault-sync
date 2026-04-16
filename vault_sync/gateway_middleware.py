"""Middleware helpers that wrap a callable with Gateway enforcement."""
from __future__ import annotations

from typing import Callable, Dict, Optional

from vault_sync.gateway import Gateway, GatewayConfig, GatewayResult


Fetcher = Callable[[str], Optional[Dict[str, str]]]


def wrap_with_gateway(fetcher: Fetcher, config: GatewayConfig) -> Fetcher:
    """Return a new fetcher that passes every call through a Gateway.

    The wrapped fetcher raises ``RuntimeError`` when the gateway rejects
    the request so callers can handle it uniformly.
    """
    class _AdaptedClient:
        """Adapts a plain fetcher callable to the interface expected by Gateway."""
        def read_secret(self, path: str) -> Optional[Dict[str, str]]:
            return fetcher(path)

    gateway = Gateway(config, _AdaptedClient())

    def _wrapped(path: str) -> Optional[Dict[str, str]]:
        result: GatewayResult = gateway.read_secret(path)
        if not result.success:
            raise RuntimeError(f"Gateway rejected request for {path!r}: {result.reason}")
        return result.value

    return _wrapped


def make_guarded_fetcher(
    fetcher: Fetcher,
    *,
    max_calls: int = 10,
    period: float = 1.0,
    burst: int = 2,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    max_duration: float = 60.0,
) -> Fetcher:
    """Convenience factory that builds a GatewayConfig and wraps *fetcher*."""
    from vault_sync.rate_limiter import RateLimitConfig
    from vault_sync.circuit_breaker import CircuitBreakerConfig
    from vault_sync.deadline import DeadlineConfig

    cfg = GatewayConfig(
        rate_limit=RateLimitConfig(max_calls=max_calls, period=period, burst=burst),
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=2,
        ),
        deadline=DeadlineConfig(max_duration=max_duration, warn_at=0.8),
    )
    return wrap_with_gateway(fetcher, cfg)
