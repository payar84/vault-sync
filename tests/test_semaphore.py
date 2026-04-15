"""Tests for vault_sync.semaphore."""
from __future__ import annotations

import threading
import time

import pytest

from vault_sync.semaphore import AcquireResult, SemaphoreConfig, VaultSemaphore


# ---------------------------------------------------------------------------
# SemaphoreConfig
# ---------------------------------------------------------------------------

def test_config_rejects_zero_max_concurrent():
    with pytest.raises(ValueError, match="max_concurrent"):
        SemaphoreConfig(max_concurrent=0).validate()


def test_config_rejects_negative_max_concurrent():
    with pytest.raises(ValueError, match="max_concurrent"):
        SemaphoreConfig(max_concurrent=-1).validate()


def test_config_rejects_zero_timeout():
    with pytest.raises(ValueError, match="timeout"):
        SemaphoreConfig(timeout=0.0).validate()


def test_config_rejects_negative_timeout():
    with pytest.raises(ValueError, match="timeout"):
        SemaphoreConfig(timeout=-5.0).validate()


def test_config_accepts_valid_values():
    cfg = SemaphoreConfig(max_concurrent=2, timeout=10.0)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# AcquireResult
# ---------------------------------------------------------------------------

def test_acquire_result_ok_is_acquired():
    r = AcquireResult.ok()
    assert r.acquired is True


def test_acquire_result_timeout_is_not_acquired():
    r = AcquireResult.timeout_error()
    assert r.acquired is False
    assert "timed out" in r.reason


def test_acquire_result_repr_ok():
    assert "True" in repr(AcquireResult.ok())


def test_acquire_result_repr_fail():
    r = AcquireResult.timeout_error()
    assert "False" in repr(r)
    assert "timed out" in repr(r)


# ---------------------------------------------------------------------------
# VaultSemaphore
# ---------------------------------------------------------------------------

def test_acquire_and_release_changes_active_count():
    sem = VaultSemaphore(config=SemaphoreConfig(max_concurrent=2, timeout=1.0))
    assert sem.active == 0
    sem.acquire()
    assert sem.active == 1
    sem.release()
    assert sem.active == 0


def test_run_executes_function():
    sem = VaultSemaphore(config=SemaphoreConfig(max_concurrent=2, timeout=1.0))
    result = sem.run(lambda: 42)
    assert result == 42


def test_run_releases_on_exception():
    sem = VaultSemaphore(config=SemaphoreConfig(max_concurrent=2, timeout=1.0))
    with pytest.raises(RuntimeError):
        sem.run(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert sem.active == 0


def test_timeout_returns_not_acquired():
    sem = VaultSemaphore(config=SemaphoreConfig(max_concurrent=1, timeout=0.05))
    sem.acquire()  # occupy the single slot
    result = sem.acquire()  # should time out
    assert result.acquired is False
    sem.release()


def test_concurrent_tasks_respect_limit():
    limit = 2
    sem = VaultSemaphore(config=SemaphoreConfig(max_concurrent=limit, timeout=5.0))
    observed_peaks: list[int] = []
    lock = threading.Lock()

    def task():
        sem.acquire()
        with lock:
            observed_peaks.append(sem.active)
        time.sleep(0.02)
        sem.release()

    threads = [threading.Thread(target=task) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert max(observed_peaks) <= limit
