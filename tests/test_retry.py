"""Tests for vault_sync.retry module."""

import pytest
from unittest.mock import MagicMock, patch
from vault_sync.retry import RetryConfig, with_retry


@pytest.fixture
def default_config():
    return RetryConfig(max_attempts=3, base_delay=0.0, max_delay=1.0)


def test_retry_config_validates_max_attempts():
    cfg = RetryConfig(max_attempts=0)
    with pytest.raises(ValueError, match="max_attempts"):
        cfg.validate()


def test_retry_config_validates_base_delay():
    cfg = RetryConfig(base_delay=-1.0)
    with pytest.raises(ValueError, match="base_delay"):
        cfg.validate()


def test_retry_config_validates_max_delay():
    cfg = RetryConfig(base_delay=5.0, max_delay=1.0)
    with pytest.raises(ValueError, match="max_delay"):
        cfg.validate()


def test_with_retry_succeeds_on_first_attempt(default_config):
    fn = MagicMock(return_value="ok")
    result = with_retry(fn, default_config)
    assert result == "ok"
    fn.assert_called_once()


def test_with_retry_retries_on_connection_error(default_config):
    fn = MagicMock(side_effect=[ConnectionError("down"), ConnectionError("down"), "ok"])
    result = with_retry(fn, default_config)
    assert result == "ok"
    assert fn.call_count == 3


def test_with_retry_raises_after_max_attempts(default_config):
    fn = MagicMock(side_effect=ConnectionError("always down"))
    with pytest.raises(RuntimeError, match="3 attempts failed"):
        with_retry(fn, default_config)
    assert fn.call_count == 3


def test_with_retry_does_not_retry_non_retryable(default_config):
    fn = MagicMock(side_effect=ValueError("bad value"))
    with pytest.raises(ValueError):
        with_retry(fn, default_config)
    fn.assert_called_once()


def test_with_retry_passes_args_and_kwargs(default_config):
    fn = MagicMock(return_value=42)
    result = with_retry(fn, default_config, "a", "b", key="val")
    fn.assert_called_once_with("a", "b", key="val")
    assert result == 42


def test_with_retry_sleeps_between_attempts():
    cfg = RetryConfig(max_attempts=2, base_delay=0.5, max_delay=10.0)
    fn = MagicMock(side_effect=[ConnectionError("err"), "ok"])
    with patch("vault_sync.retry.time.sleep") as mock_sleep:
        with_retry(fn, cfg)
        mock_sleep.assert_called_once_with(0.5)
