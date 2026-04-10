"""Tests for vault_sync.rotation."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from vault_sync.rotation import RotationPolicy, RotationStatus, RotationTracker


@pytest.fixture
def policy() -> RotationPolicy:
    return RotationPolicy(max_age_days=30, warn_before_days=7)


@pytest.fixture
def tracker(policy: RotationPolicy) -> RotationTracker:
    return RotationTracker(policy=policy)


def test_policy_validates_max_age_days():
    with pytest.raises(ValueError, match="max_age_days"):
        RotationPolicy(max_age_days=0).validate()


def test_policy_validates_warn_before_days():
    with pytest.raises(ValueError, match="warn_before_days"):
        RotationPolicy(max_age_days=30, warn_before_days=0).validate()


def test_policy_warn_must_be_less_than_max_age():
    with pytest.raises(ValueError, match="less than"):
        RotationPolicy(max_age_days=10, warn_before_days=10).validate()


def test_unknown_key_is_expired(tracker: RotationTracker):
    status = tracker.check("UNKNOWN_KEY")
    assert status.is_expired is True
    assert status.last_rotated is None
    assert status.days_until_expiry is None


def test_recently_rotated_key_is_ok(tracker: RotationTracker):
    tracker.record_rotation("DB_PASSWORD", datetime.utcnow())
    status = tracker.check("DB_PASSWORD")
    assert status.is_expired is False
    assert status.is_expiring_soon is False
    assert status.days_until_expiry is not None and status.days_until_expiry > 7


def test_old_key_is_expired(tracker: RotationTracker):
    old = datetime.utcnow() - timedelta(days=60)
    tracker.record_rotation("OLD_KEY", old)
    status = tracker.check("OLD_KEY")
    assert status.is_expired is True
    assert status.days_until_expiry is None


def test_key_expiring_soon(tracker: RotationTracker):
    soon = datetime.utcnow() - timedelta(days=25)
    tracker.record_rotation("SOON_KEY", soon)
    status = tracker.check("SOON_KEY")
    assert status.is_expiring_soon is True
    assert status.is_expired is False


def test_check_all_returns_all_statuses(tracker: RotationTracker):
    tracker.record_rotation("KEY_A", datetime.utcnow())
    statuses = tracker.check_all(["KEY_A", "KEY_B"])
    assert len(statuses) == 2
    assert statuses[0].key == "KEY_A"
    assert statuses[1].key == "KEY_B"


def test_expired_keys_filters_correctly(tracker: RotationTracker):
    tracker.record_rotation("FRESH", datetime.utcnow())
    expired = tracker.expired_keys(["FRESH", "MISSING"])
    assert expired == ["MISSING"]


def test_expiring_soon_keys_filters_correctly(tracker: RotationTracker):
    tracker.record_rotation("SOON", datetime.utcnow() - timedelta(days=25))
    tracker.record_rotation("FRESH", datetime.utcnow())
    result = tracker.expiring_soon_keys(["SOON", "FRESH"])
    assert result == ["SOON"]


def test_repr_expired():
    s = RotationStatus("K", None, is_expired=True, is_expiring_soon=False, days_until_expiry=None)
    assert "expired" in repr(s)


def test_repr_ok():
    s = RotationStatus("K", datetime.utcnow(), is_expired=False, is_expiring_soon=False, days_until_expiry=20)
    assert "ok" in repr(s)
