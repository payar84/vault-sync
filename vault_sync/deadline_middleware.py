"""Middleware that wraps a callable and aborts if a deadline is exceeded."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from vault_sync.deadline import Deadline, make_deadline


class DeadlineExceededError(RuntimeError):
    """Raised when an operation exceeds its configured deadline."""


@dataclass
class DeadlineMiddlewareResult:
    success: bool
    value: Any
    error: Optional[str]

    @classmethod
    def ok(cls, value: Any) -> "DeadlineMiddlewareResult":
        return cls(success=True, value=value, error=None)

    @classmethod
    def fail(cls, reason: str) -> "DeadlineMiddlewareResult":
        return cls(success=False, value=None, error=reason)

    def __repr__(self) -> str:
        if self.success:
            return f"<DeadlineMiddlewareResult OK value={self.value!r}>"
        return f"<DeadlineMiddlewareResult FAIL error={self.error!r}>"


def with_deadline(
    fn: Callable[..., Any],
    deadline: Deadline,
    *args: Any,
    **kwargs: Any,
) -> DeadlineMiddlewareResult:
    """Call *fn* only if the deadline has not expired; raise otherwise."""
    if deadline.is_expired():
        raise DeadlineExceededError(
            f"Deadline of {deadline.config.max_duration_seconds}s already exceeded "
            f"before call (elapsed {deadline.elapsed():.2f}s)"
        )
    try:
        result = fn(*args, **kwargs)
        return DeadlineMiddlewareResult.ok(result)
    except Exception as exc:  # noqa: BLE001
        return DeadlineMiddlewareResult.fail(str(exc))


def guarded(
    max_seconds: float,
    warn_at: float = 0.8,
) -> Callable[[Callable[..., Any]], Callable[..., DeadlineMiddlewareResult]]:
    """Decorator factory that enforces a deadline on the wrapped function."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., DeadlineMiddlewareResult]:
        dl = make_deadline(max_seconds, warn_at)

        def wrapper(*args: Any, **kwargs: Any) -> DeadlineMiddlewareResult:
            return with_deadline(fn, dl, *args, **kwargs)

        wrapper.__name__ = fn.__name__
        return wrapper

    return decorator
