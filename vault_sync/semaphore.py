"""Concurrency semaphore for limiting parallel Vault operations."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class SemaphoreConfig:
    max_concurrent: int = 4
    timeout: float = 30.0

    def validate(self) -> None:
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


@dataclass
class AcquireResult:
    acquired: bool
    reason: str = ""

    @staticmethod
    def ok() -> "AcquireResult":
        return AcquireResult(acquired=True)

    @staticmethod
    def timeout_error() -> "AcquireResult":
        return AcquireResult(acquired=False, reason="timed out waiting for semaphore")

    def __repr__(self) -> str:
        if self.acquired:
            return "AcquireResult(acquired=True)"
        return f"AcquireResult(acquired=False, reason={self.reason!r})"


@dataclass
class VaultSemaphore:
    config: SemaphoreConfig
    _sem: threading.Semaphore = field(init=False)
    _lock: threading.Lock = field(init=False, default_factory=threading.Lock)
    _active: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.config.validate()
        self._sem = threading.Semaphore(self.config.max_concurrent)
        self._lock = threading.Lock()

    @property
    def active(self) -> int:
        with self._lock:
            return self._active

    def acquire(self) -> AcquireResult:
        acquired = self._sem.acquire(timeout=self.config.timeout)
        if not acquired:
            return AcquireResult.timeout_error()
        with self._lock:
            self._active += 1
        return AcquireResult.ok()

    def release(self) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)
        self._sem.release()

    def run(self, fn: Callable[[], T]) -> T:
        result = self.acquire()
        if not result.acquired:
            raise RuntimeError(result.reason)
        try:
            return fn()
        finally:
            self.release()
