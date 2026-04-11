"""Tests for vault_sync.hooks."""
import pytest
from vault_sync.hooks import (
    HookConfig,
    HookResult,
    run_hook,
    run_hooks,
    all_ok,
)


# ---------------------------------------------------------------------------
# HookConfig
# ---------------------------------------------------------------------------

def test_hook_config_defaults():
    cfg = HookConfig()
    assert cfg.pre_sync == []
    assert cfg.post_sync == []
    assert cfg.timeout == 30


def test_hook_config_validates_timeout():
    cfg = HookConfig(timeout=0)
    with pytest.raises(ValueError, match="timeout"):
        cfg.validate()


def test_hook_config_negative_timeout_invalid():
    cfg = HookConfig(timeout=-5)
    with pytest.raises(ValueError):
        cfg.validate()


def test_hook_config_valid_passes():
    cfg = HookConfig(pre_sync=["echo hi"], timeout=10)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# HookResult
# ---------------------------------------------------------------------------

def test_hook_result_ok_when_zero():
    r = HookResult(command="echo", returncode=0, stdout="", stderr="")
    assert r.ok is True


def test_hook_result_not_ok_when_nonzero():
    r = HookResult(command="false", returncode=1, stdout="", stderr="")
    assert r.ok is False


def test_hook_result_repr_ok():
    r = HookResult(command="echo hi", returncode=0, stdout="hi", stderr="")
    assert "ok" in repr(r)


def test_hook_result_repr_failed():
    r = HookResult(command="bad", returncode=2, stdout="", stderr="err")
    assert "failed(2)" in repr(r)


# ---------------------------------------------------------------------------
# run_hook
# ---------------------------------------------------------------------------

def test_run_hook_success():
    result = run_hook("echo hello")
    assert result.ok
    assert result.stdout == "hello"


def test_run_hook_failure():
    result = run_hook("exit 1", timeout=5)
    assert not result.ok
    assert result.returncode == 1


def test_run_hook_timeout():
    result = run_hook("sleep 10", timeout=1)
    assert not result.ok
    assert result.returncode == -1
    assert "timeout" in result.stderr


# ---------------------------------------------------------------------------
# run_hooks
# ---------------------------------------------------------------------------

def test_run_hooks_all_succeed():
    results = run_hooks(["echo a", "echo b"])
    assert len(results) == 2
    assert all_ok(results)


def test_run_hooks_stops_on_failure():
    results = run_hooks(["echo a", "exit 1", "echo c"])
    # third command should not run
    assert len(results) == 2
    assert results[0].ok
    assert not results[1].ok


def test_all_ok_empty_list():
    assert all_ok([]) is True
