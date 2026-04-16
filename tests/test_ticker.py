import pytest
from vault_sync.ticker import TickerConfig, TickerState, TickEvent


@pytest.fixture
def config():
    return TickerConfig(interval_seconds=1.0, max_ticks=3)


@pytest.fixture
def state(config):
    return TickerState(config=config)


def test_config_rejects_zero_interval():
    with pytest.raises(ValueError, match="interval_seconds"):
        TickerConfig(interval_seconds=0).validate()


def test_config_rejects_negative_interval():
    with pytest.raises(ValueError, match="interval_seconds"):
        TickerConfig(interval_seconds=-1.0).validate()


def test_config_rejects_zero_max_ticks():
    with pytest.raises(ValueError, match="max_ticks"):
        TickerConfig(interval_seconds=1.0, max_ticks=0).validate()


def test_config_accepts_valid_values():
    cfg = TickerConfig(interval_seconds=0.5, max_ticks=5)
    cfg.validate()


def test_config_accepts_none_max_ticks():
    cfg = TickerConfig(interval_seconds=1.0)
    cfg.validate()
    assert cfg.max_ticks is None


def test_initial_count_is_zero(state):
    assert state.count == 0


def test_tick_increments_count(state):
    state.tick()
    assert state.count == 1


def test_tick_returns_event(state):
    event = state.tick()
    assert isinstance(event, TickEvent)
    assert event.tick == 1


def test_tick_numbers_are_sequential(state):
    e1 = state.tick()
    e2 = state.tick()
    assert e1.tick == 1
    assert e2.tick == 2


def test_last_returns_most_recent(state):
    state.tick()
    e = state.tick()
    assert state.last() == e


def test_last_is_none_when_empty(state):
    assert state.last() is None


def test_is_done_false_before_max(state):
    state.tick()
    assert not state.is_done()


def test_is_done_true_at_max(state):
    for _ in range(3):
        state.tick()
    assert state.is_done()


def test_is_done_false_when_no_max():
    s = TickerState(config=TickerConfig(interval_seconds=1.0))
    for _ in range(100):
        s.tick()
    assert not s.is_done()


def test_history_returns_all_events(state):
    state.tick()
    state.tick()
    h = state.history()
    assert len(h) == 2


def test_event_to_dict_contains_keys():
    e = TickEvent(tick=1, fired_at="2024-01-01T00:00:00+00:00")
    d = e.to_dict()
    assert "tick" in d
    assert "fired_at" in d
