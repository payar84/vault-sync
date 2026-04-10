"""Tests for vault_sync.watcher."""

import pytest
from unittest.mock import MagicMock, call

from vault_sync.watcher import WatchConfig, WatchResult, run_watcher


# ---------------------------------------------------------------------------
# WatchConfig validation
# ---------------------------------------------------------------------------

def test_watch_config_rejects_zero_interval():
    cfg = WatchConfig(interval_seconds=0)
    with pytest.raises(ValueError, match="interval_seconds"):
        cfg.validate()


def test_watch_config_rejects_negative_interval():
    cfg = WatchConfig(interval_seconds=-5.0)
    with pytest.raises(ValueError, match="interval_seconds"):
        cfg.validate()


def test_watch_config_rejects_zero_max_iterations():
    cfg = WatchConfig(max_iterations=0)
    with pytest.raises(ValueError, match="max_iterations"):
        cfg.validate()


def test_watch_config_accepts_none_max_iterations():
    cfg = WatchConfig(interval_seconds=10.0, max_iterations=None)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# WatchResult helpers
# ---------------------------------------------------------------------------

def test_record_sync_increments_counts():
    r = WatchResult()
    r.record_sync()
    assert r.iterations == 1
    assert r.sync_count == 1
    assert r.error_count == 0


def test_record_error_increments_counts():
    r = WatchResult()
    r.record_error("boom")
    assert r.iterations == 1
    assert r.error_count == 1
    assert r.errors == ["boom"]


def test_watch_result_repr():
    r = WatchResult(iterations=3, sync_count=2, error_count=1)
    assert "iterations=3" in repr(r)
    assert "syncs=2" in repr(r)
    assert "errors=1" in repr(r)


# ---------------------------------------------------------------------------
# run_watcher behaviour
# ---------------------------------------------------------------------------

def _make_sleep() -> MagicMock:
    return MagicMock()


def test_run_watcher_calls_sync_fn_correct_times():
    sync_fn = MagicMock()
    sleep_fn = _make_sleep()
    cfg = WatchConfig(interval_seconds=1.0, max_iterations=3)

    result = run_watcher(cfg, sync_fn, sleep_fn=sleep_fn)

    assert sync_fn.call_count == 3
    assert result.sync_count == 3
    assert result.iterations == 3


def test_run_watcher_sleeps_between_iterations():
    sync_fn = MagicMock()
    sleep_fn = _make_sleep()
    cfg = WatchConfig(interval_seconds=5.0, max_iterations=3)

    run_watcher(cfg, sync_fn, sleep_fn=sleep_fn)

    # Sleep is called after each iteration except the last
    assert sleep_fn.call_count == 2
    sleep_fn.assert_called_with(5.0)


def test_run_watcher_handles_sync_errors():
    sync_fn = MagicMock(side_effect=RuntimeError("vault unreachable"))
    sleep_fn = _make_sleep()
    cfg = WatchConfig(interval_seconds=1.0, max_iterations=2)

    result = run_watcher(cfg, sync_fn, sleep_fn=sleep_fn)

    assert result.error_count == 2
    assert result.sync_count == 0
    assert "vault unreachable" in result.errors[0]


def test_run_watcher_mixed_success_and_error():
    sync_fn = MagicMock(side_effect=[None, RuntimeError("fail"), None])
    sleep_fn = _make_sleep()
    cfg = WatchConfig(interval_seconds=1.0, max_iterations=3)

    result = run_watcher(cfg, sync_fn, sleep_fn=sleep_fn)

    assert result.sync_count == 2
    assert result.error_count == 1
    assert result.iterations == 3
