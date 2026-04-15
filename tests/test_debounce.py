"""Tests for vault_sync.debounce."""
import time
import pytest
from vault_sync.debounce import Debounce
Config = None  # resolved below

from vault_sync.debounce import DebounceConfig, DebounceState, Debouncer


# ---------------------------------------------------------------------------
# DebounceConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_window():
    with pytest.raises(ValueError, match="window_seconds"):
        DebounceConfig(window_seconds=0).validate()


def test_config_rejects_negative_window():
    with pytest.raises(ValueError, match="window_seconds"):
        DebounceConfig(window_seconds=-1.0).validate()


def test_config_rejects_zero_max_pending():
    with pytest.raises(ValueError, match="max_pending"):
        DebounceConfig(max_pending=0).validate()


def test_config_accepts_valid_values():
    cfg = DebounceConfig(window_seconds=0.5, max_pending=50)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# DebounceState
# ---------------------------------------------------------------------------

def test_state_initial_count_is_one():
    s = DebounceState(path="secret/app")
    assert s.count == 1


def test_state_touch_increments_count():
    s = DebounceState(path="secret/app")
    s.touch()
    assert s.count == 2


def test_state_repr_contains_path():
    s = DebounceState(path="secret/app")
    assert "secret/app" in repr(s)


# ---------------------------------------------------------------------------
# Debouncer.push
# ---------------------------------------------------------------------------

def test_push_returns_true_for_new_path():
    d = Debouncer(DebounceConfig(window_seconds=1.0))
    assert d.push("secret/db") is True


def test_push_returns_true_for_existing_path():
    d = Debouncer(DebounceConfig(window_seconds=1.0))
    d.push("secret/db")
    assert d.push("secret/db") is True


def test_push_increments_count_on_repeat():
    d = Debouncer(DebounceConfig(window_seconds=1.0))
    d.push("secret/db")
    d.push("secret/db")
    assert d._pending["secret/db"].count == 2


def test_push_returns_false_when_queue_full():
    d = Debouncer(DebounceConfig(window_seconds=1.0, max_pending=2))
    d.push("a")
    d.push("b")
    assert d.push("c") is False


def test_pending_count_reflects_queue_size():
    d = Debouncer(DebounceConfig(window_seconds=1.0))
    d.push("x")
    d.push("y")
    assert d.pending_count() == 2


# ---------------------------------------------------------------------------
# Debouncer.ready
# ---------------------------------------------------------------------------

def test_ready_returns_empty_before_window_elapses():
    d = Debouncer(DebounceConfig(window_seconds=60.0))
    d.push("secret/app")
    assert d.ready() == []


def test_ready_returns_path_after_window():
    d = Debouncer(DebounceConfig(window_seconds=0.1))
    d.push("secret/app")
    future = time.monotonic() + 1.0
    result = d.ready(now=future)
    assert "secret/app" in result


def test_ready_removes_returned_paths():
    d = Debouncer(DebounceConfig(window_seconds=0.1))
    d.push("secret/app")
    future = time.monotonic() + 1.0
    d.ready(now=future)
    assert d.pending_count() == 0


def test_ready_result_is_sorted():
    d = Debouncer(DebounceConfig(window_seconds=0.1))
    d.push("z/path")
    d.push("a/path")
    future = time.monotonic() + 1.0
    result = d.ready(now=future)
    assert result == sorted(result)


# ---------------------------------------------------------------------------
# Debouncer.clear
# ---------------------------------------------------------------------------

def test_clear_empties_queue():
    d = Debouncer(DebounceConfig(window_seconds=1.0))
    d.push("secret/app")
    d.clear()
    assert d.pending_count() == 0
