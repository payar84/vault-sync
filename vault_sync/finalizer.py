"""Finalizer: run cleanup callbacks after a sync operation completes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class FinalizerConfig:
    stop_on_error: bool = False
    max_callbacks: int = 32

    def validate(self) -> None:
        if self.max_callbacks < 1:
            raise ValueError("max_callbacks must be >= 1")


@dataclass
class FinalizerResult:
    ran: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.ok else f"{len(self.errors)} error(s)"
        return f"<FinalizerResult ran={self.ran} status={status}>"


class Finalizer:
    """Collects callbacks and runs them in registration order."""

    def __init__(self, config: Optional[FinalizerConfig] = None) -> None:
        self._config = config or FinalizerConfig()
        self._config.validate()
        self._callbacks: List[Callable[[], None]] = []

    def register(self, fn: Callable[[], None]) -> None:
        """Register a cleanup callback.  Raises if the cap is reached."""
        if len(self._callbacks) >= self._config.max_callbacks:
            raise RuntimeError(
                f"Finalizer callback cap ({self._config.max_callbacks}) reached"
            )
        self._callbacks.append(fn)

    def run(self) -> FinalizerResult:
        """Execute all registered callbacks and return a result summary."""
        result = FinalizerResult()
        for fn in self._callbacks:
            try:
                fn()
                result.ran += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(str(exc))
                result.ran += 1
                if self._config.stop_on_error:
                    break
        return result

    def clear(self) -> None:
        """Remove all registered callbacks."""
        self._callbacks.clear()

    @property
    def count(self) -> int:
        return len(self._callbacks)
