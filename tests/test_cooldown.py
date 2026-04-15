"""Tests for vault_sync.cooldown."""
from __future__ import annotations

import pytest

from vault_sync.cooldown import Cooldown, CooldownConfig, CooldownStatus


@pytest.fixture()
def config() -> CooldownConfig:
    return CooldownConfig(min_interval_seconds=30.0, max_tracked_paths=100)


@pytest.fixture()
def cooldown(config: CooldownConfig) -> Cooldown:
    return Cooldown(config=config)


def test_config_rejects_zero_interval():
    with pytest.raises(ValueError, match="min_interval_seconds"):
        CooldownConfig(min_interval_seconds=0).validate()


def test_config_rejects_negative_interval():
    with pytest.raises(ValueError, match="min_interval_seconds"):
        CooldownConfig(min_interval_seconds=-1.0).validate()


def test_config_rejects_zero_max_paths():
    with pytest.raises(ValueError, match="max_tracked_paths"):
        CooldownConfig(max_tracked_paths=0).validate()


def test_config_accepts_valid_values():
    CooldownConfig(min_interval_seconds=10.0, max_tracked_paths=50).validate()


def test_untracked_path_is_ready(cooldown: Cooldown):
    status = cooldown.check("secret/app", now=1000.0)
    assert status.ready is True
    assert status.seconds_remaining == 0.0
    assert status.last_synced_at is None


def test_recently_synced_path_is_not_ready(cooldown: Cooldown):
    cooldown.record("secret/app", now=1000.0)
    status = cooldown.check("secret/app", now=1010.0)
    assert status.ready is False
    assert status.seconds_remaining == pytest.approx(20.0)


def test_path_becomes_ready_after_interval(cooldown: Cooldown):
    cooldown.record("secret/app", now=1000.0)
    status = cooldown.check("secret/app", now=1031.0)
    assert status.ready is True
    assert status.seconds_remaining == 0.0


def test_is_ready_convenience_method(cooldown: Cooldown):
    assert cooldown.is_ready("secret/x", now=500.0) is True
    cooldown.record("secret/x", now=500.0)
    assert cooldown.is_ready("secret/x", now=510.0) is False


def test_clear_removes_record(cooldown: Cooldown):
    cooldown.record("secret/app", now=1000.0)
    removed = cooldown.clear("secret/app")
    assert removed is True
    assert cooldown.is_ready("secret/app", now=1005.0) is True


def test_clear_returns_false_for_unknown_path(cooldown: Cooldown):
    assert cooldown.clear("secret/missing") is False


def test_tracked_paths_returns_sorted_list(cooldown: Cooldown):
    cooldown.record("secret/z", now=1.0)
    cooldown.record("secret/a", now=2.0)
    assert cooldown.tracked_paths() == ["secret/a", "secret/z"]


def test_evicts_oldest_when_capacity_reached():
    cfg = CooldownConfig(min_interval_seconds=60.0, max_tracked_paths=2)
    cd = Cooldown(config=cfg)
    cd.record("secret/first", now=1.0)
    cd.record("secret/second", now=2.0)
    cd.record("secret/third", now=3.0)  # should evict 'first'
    assert len(cd.tracked_paths()) == 2
    assert "secret/first" not in cd.tracked_paths()


def test_status_repr_ready(cooldown: Cooldown):
    status = cooldown.check("secret/app", now=1000.0)
    assert "ready" in repr(status)


def test_status_repr_cooling(cooldown: Cooldown):
    cooldown.record("secret/app", now=1000.0)
    status = cooldown.check("secret/app", now=1005.0)
    assert "cooling" in repr(status)
