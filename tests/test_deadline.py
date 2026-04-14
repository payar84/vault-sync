"""Tests for vault_sync.deadline."""
from __future__ import annotations

import time

import pytest

from vault_sync.deadline import DeadlineConfig, DeadlineStatus, Deadline, make_deadline


# ---------------------------------------------------------------------------
# DeadlineConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_max_duration():
    with pytest.raises(ValueError, match="max_duration_seconds"):
        DeadlineConfig(max_duration_seconds=0).validate()


def test_config_rejects_negative_max_duration():
    with pytest.raises(ValueError, match="max_duration_seconds"):
        DeadlineConfig(max_duration_seconds=-1).validate()


def test_config_rejects_warn_at_zero():
    with pytest.raises(ValueError, match="warn_at_fraction"):
        DeadlineConfig(max_duration_seconds=10, warn_at_fraction=0.0).validate()


def test_config_rejects_warn_at_one():
    with pytest.raises(ValueError, match="warn_at_fraction"):
        DeadlineConfig(max_duration_seconds=10, warn_at_fraction=1.0).validate()


def test_config_accepts_valid_values():
    cfg = DeadlineConfig(max_duration_seconds=30, warn_at_fraction=0.75)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# Deadline behaviour
# ---------------------------------------------------------------------------

def test_make_deadline_returns_deadline_instance():
    dl = make_deadline(10)
    assert isinstance(dl, Deadline)


def test_fresh_deadline_is_not_expired():
    dl = make_deadline(60)
    assert not dl.is_expired()


def test_fresh_deadline_is_not_warned():
    dl = make_deadline(60, warn_at=0.9)
    assert not dl.is_warned()


def test_elapsed_increases_over_time():
    dl = make_deadline(60)
    t1 = dl.elapsed()
    time.sleep(0.05)
    t2 = dl.elapsed()
    assert t2 > t1


def test_status_expired_flag_set_after_expiry(monkeypatch):
    dl = make_deadline(1.0)
    monkeypatch.setattr("vault_sync.deadline.time.monotonic", lambda: dl._start + 2.0)
    status = dl.status()
    assert status.expired is True


def test_status_warned_flag_set_before_expiry(monkeypatch):
    dl = make_deadline(10.0, warn_at=0.5)
    monkeypatch.setattr("vault_sync.deadline.time.monotonic", lambda: dl._start + 6.0)
    status = dl.status()
    assert status.warned is True
    assert status.expired is False


def test_status_remaining_is_zero_when_expired(monkeypatch):
    dl = make_deadline(5.0)
    monkeypatch.setattr("vault_sync.deadline.time.monotonic", lambda: dl._start + 10.0)
    assert dl.status().remaining == 0.0


def test_status_remaining_positive_when_within_limit(monkeypatch):
    dl = make_deadline(10.0)
    monkeypatch.setattr("vault_sync.deadline.time.monotonic", lambda: dl._start + 3.0)
    assert dl.status().remaining == pytest.approx(7.0)


def test_reset_restarts_elapsed_time():
    dl = make_deadline(60)
    time.sleep(0.05)
    dl.reset()
    assert dl.elapsed() < 0.05


def test_status_repr_contains_state():
    dl = make_deadline(60)
    r = repr(dl.status())
    assert "OK" in r or "WARN" in r or "EXPIRED" in r
