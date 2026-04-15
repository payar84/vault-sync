"""Tests for vault_sync.throttle."""
from __future__ import annotations

import time
import pytest

from vault_sync.throttle import ThrottleConfig, Throttle, ThrottleState, build_throttle


# ---------------------------------------------------------------------------
# ThrottleConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_min_interval():
    with pytest.raises(ValueError, match="min_interval"):
        ThrottleConfig(min_interval=0.0).validate()


def test_config_rejects_negative_min_interval():
    with pytest.raises(ValueError, match="min_interval"):
        ThrottleConfig(min_interval=-0.5).validate()


def test_config_rejects_zero_max_burst():
    with pytest.raises(ValueError, match="max_burst"):
        ThrottleConfig(max_burst=0).validate()


def test_config_accepts_valid_values():
    cfg = ThrottleConfig(min_interval=0.05, max_burst=3)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# Throttle burst behaviour
# ---------------------------------------------------------------------------

def test_burst_calls_are_not_delayed():
    throttle = Throttle(ThrottleConfig(min_interval=1.0, max_burst=3))
    results = [throttle.acquire() for _ in range(3)]
    assert all(delayed is False for delayed in results)


def test_call_beyond_burst_is_delayed(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # Force elapsed to be 0 so a delay is always needed after burst
    monkeypatch.setattr(time, "monotonic", lambda: 0.0)

    throttle = Throttle(ThrottleConfig(min_interval=0.2, max_burst=2))
    # Exhaust burst
    throttle.acquire()
    throttle.acquire()
    # Next call should be delayed
    delayed = throttle.acquire()
    assert delayed is True
    assert len(slept) == 1
    assert slept[0] == pytest.approx(0.2, abs=1e-6)


def test_burst_of_one_delays_second_call(monkeypatch):
    """A max_burst=1 throttle should delay every call after the first."""
    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(time, "monotonic", lambda: 0.0)

    throttle = Throttle(ThrottleConfig(min_interval=0.1, max_burst=1))
    first = throttle.acquire()
    second = throttle.acquire()

    assert first is False
    assert second is True
    assert len(slept) == 1


# ---------------------------------------------------------------------------
# ThrottleState counters
# ---------------------------------------------------------------------------

def test_total_calls_increments(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda _: None)
    monkeypatch.setattr(time, "monotonic", lambda: 0.0)
    throttle = Throttle(ThrottleConfig(min_interval=0.1, max_burst=1))
    for _ in range(4):
        throttle.acquire()
    assert throttle.state.total_calls == 4


def test_total_delayed_increments(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda _: None)
    monkeypatch.setattr(time, "monotonic", lambda: 0.0)
    throttle = Throttle(ThrottleConfig(min_interval=0.1, max_burst=1))
    throttle.acquire()  # burst – not delayed
    throttle.acquire()  # delayed
    throttle.acquire()  # delayed
    assert throttle.state.total_delayed == 2


# ---------------------------------------------------------------------------
# wrap helper
# ------------------------------------------
