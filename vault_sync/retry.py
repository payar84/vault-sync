"""Retry logic for Vault client operations with exponential backoff."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 10.0
    backoff_factor: float = 2.0
    retryable_exceptions: tuple = field(
        default_factory=lambda: (ConnectionError, TimeoutError)
    )

    def validate(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")


def with_retry(fn: Callable[..., T], config: RetryConfig, *args: Any, **kwargs: Any) -> T:
    """Call fn with retry logic based on RetryConfig."""
    config.validate()
    last_exc: Exception | None = None
    delay = config.base_delay

    for attempt in range(1, config.max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except config.retryable_exceptions as exc:
            last_exc = exc
            if attempt == config.max_attempts:
                break
            logger.warning(
                "Attempt %d/%d failed: %s. Retrying in %.1fs...",
                attempt,
                config.max_attempts,
                exc,
                delay,
            )
            time.sleep(delay)
            delay = min(delay * config.backoff_factor, config.max_delay)

    raise RuntimeError(
        f"All {config.max_attempts} attempts failed"
    ) from last_exc
