"""Tests for vault_sync.finalizer."""
from __future__ import annotations

import pytest

from vault_sync.finalizer import Finalizer, FinalizerConfig, FinalizerResult


# ---------------------------------------------------------------------------
# FinalizerConfig
# ---------------------------------------------------------------------------

def test_config_rejects_zero_max_callbacks():
    with pytest.raises(ValueError, match="max_callbacks"):
        FinalizerConfig(max_callbacks=0).validate()


def test_config_rejects_negative_max_callbacks():
    with pytest.raises(ValueError):
        FinalizerConfig(max_callbacks=-1).validate()


def test_config_accepts_valid_values():
    cfg = FinalizerConfig(stop_on_error=True, max_callbacks=10)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# FinalizerResult
# ---------------------------------------------------------------------------

def test_result_ok_when_no_errors():
    r = FinalizerResult(ran=3)
    assert r.ok is True


def test_result_not_ok_when_errors():
    r = FinalizerResult(ran=1, errors=["boom"])
    assert r.ok is False


# ---------------------------------------------------------------------------
# Finalizer.register
# ---------------------------------------------------------------------------

def test_register_increases_count():
    f = Finalizer()
    f.register(lambda: None)
    assert f.count == 1


def test_register_raises_when_cap_reached():
    cfg = FinalizerConfig(max_callbacks=2)
    f = Finalizer(cfg)
    f.register(lambda: None)
    f.register(lambda: None)
    with pytest.raises(RuntimeError, match="cap"):
        f.register(lambda: None)


def test_clear_removes_all_callbacks():
    f = Finalizer()
    f.register(lambda: None)
    f.register(lambda: None)
    f.clear()
    assert f.count == 0


# ---------------------------------------------------------------------------
# Finalizer.run
# ---------------------------------------------------------------------------

def test_run_executes_all_callbacks():
    called = []
    f = Finalizer()
    f.register(lambda: called.append(1))
    f.register(lambda: called.append(2))
    result = f.run()
    assert called == [1, 2]
    assert result.ran == 2
    assert result.ok is True


def test_run_captures_errors_by_default():
    f = Finalizer()
    f.register(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
    f.register(lambda: None)  # should still run
    result = f.run()
    assert result.ran == 2
    assert len(result.errors) == 1
    assert "fail" in result.errors[0]


def test_stop_on_error_halts_chain():
    called = []
    cfg = FinalizerConfig(stop_on_error=True)
    f = Finalizer(cfg)
    f.register(lambda: (_ for _ in ()).throw(RuntimeError("stop")))
    f.register(lambda: called.append("should not run"))
    result = f.run()
    assert called == []
    assert result.ran == 1
    assert not result.ok


def test_run_with_no_callbacks_returns_ok():
    f = Finalizer()
    result = f.run()
    assert result.ran == 0
    assert result.ok is True
