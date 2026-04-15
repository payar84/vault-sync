import pytest
from vault_sync.heartbeat import Heartbeat, HeartbeatConfig, HeartbeatStatus
from datetime import datetime


@pytest.fixture
def config():
    return HeartbeatConfig(interval_seconds=10.0, max_misses=3, label="test")


@pytest.fixture
def hb(config):
    return Heartbeat(config=config)


def test_config_rejects_zero_interval():
    cfg = HeartbeatConfig(interval_seconds=0)
    with pytest.raises(ValueError, match="interval_seconds"):
        cfg.validate()


def test_config_rejects_negative_interval():
    cfg = HeartbeatConfig(interval_seconds=-1.0)
    with pytest.raises(ValueError, match="interval_seconds"):
        cfg.validate()


def test_config_rejects_zero_max_misses():
    cfg = HeartbeatConfig(max_misses=0)
    with pytest.raises(ValueError, match="max_misses"):
        cfg.validate()


def test_config_rejects_blank_label():
    cfg = HeartbeatConfig(label="   ")
    with pytest.raises(ValueError, match="label"):
        cfg.validate()


def test_config_accepts_valid_values():
    cfg = HeartbeatConfig(interval_seconds=5.0, max_misses=2, label="svc")
    cfg.validate()  # should not raise


def test_initial_status_is_alive(hb):
    assert hb.is_alive() is True


def test_initial_miss_count_is_zero(hb):
    assert hb.status().miss_count == 0


def test_initial_last_beat_is_none(hb):
    assert hb.status().last_beat is None


def test_beat_sets_last_beat(hb):
    hb.beat()
    assert hb.status().last_beat is not None
    assert isinstance(hb.status().last_beat, datetime)


def test_beat_resets_miss_count(hb):
    hb.miss()
    hb.miss()
    hb.beat()
    assert hb.status().miss_count == 0


def test_miss_increments_count(hb):
    hb.miss()
    assert hb.status().miss_count == 1


def test_exceeding_max_misses_marks_dead(hb):
    for _ in range(3):
        hb.miss()
    assert hb.is_alive() is False


def test_below_max_misses_stays_alive(hb):
    hb.miss()
    hb.miss()
    assert hb.is_alive() is True


def test_reset_clears_state(hb):
    hb.beat()
    hb.miss()
    hb.reset()
    s = hb.status()
    assert s.last_beat is None
    assert s.miss_count == 0


def test_status_repr_contains_label(hb):
    r = repr(hb.status())
    assert "test" in r


def test_status_repr_shows_alive(hb):
    r = repr(hb.status())
    assert "alive" in r
