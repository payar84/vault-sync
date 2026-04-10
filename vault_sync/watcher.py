"""File watcher that triggers re-sync when Vault secrets change."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class WatchConfig:
    interval_seconds: float = 30.0
    max_iterations: Optional[int] = None  # None means run forever

    def validate(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.max_iterations is not None and self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")


@dataclass
class WatchResult:
    iterations: int = 0
    sync_count: int = 0
    error_count: int = 0
    errors: list[str] = field(default_factory=list)

    def record_sync(self) -> None:
        self.iterations += 1
        self.sync_count += 1

    def record_error(self, message: str) -> None:
        self.iterations += 1
        self.error_count += 1
        self.errors.append(message)

    def __repr__(self) -> str:
        return (
            f"WatchResult(iterations={self.iterations}, "
            f"syncs={self.sync_count}, errors={self.error_count})"
        )


def run_watcher(
    config: WatchConfig,
    sync_fn: Callable[[], None],
    sleep_fn: Callable[[float], None] = time.sleep,
) -> WatchResult:
    """Run a polling loop that calls sync_fn on each interval.

    Args:
        config: Watch configuration (interval, max iterations).
        sync_fn: Callable that performs the sync; may raise exceptions.
        sleep_fn: Injectable sleep function (for testing).

    Returns:
        WatchResult summarising the run.
    """
    config.validate()
    result = WatchResult()
    iteration = 0

    while True:
        try:
            logger.info("Running sync (iteration %d)", iteration + 1)
            sync_fn()
            result.record_sync()
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            logger.error("Sync error: %s", msg)
            result.record_error(msg)

        iteration += 1
        if config.max_iterations is not None and iteration >= config.max_iterations:
            break

        sleep_fn(config.interval_seconds)

    return result
