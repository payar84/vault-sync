"""Tests for vault_sync.health module."""

import pytest
from unittest.mock import MagicMock
from vault_sync.health import HealthStatus, check_health
from vault_sync.retry import RetryConfig


@pytest.fixture
def fast_retry():
    return RetryConfig(max_attempts=1, base_delay=0.0)


@pytest.fixture
def mock_client():
    return MagicMock()


def test_health_status_ok_when_reachable_and_authenticated():
    status = HealthStatus(reachable=True, authenticated=True)
    assert status.ok is True


def test_health_status_not_ok_if_not_authenticated():
    status = HealthStatus(reachable=True, authenticated=False)
    assert status.ok is False


def test_health_status_not_ok_if_not_reachable():
    status = HealthStatus(reachable=False, authenticated=False)
    assert status.ok is False


def test_health_status_repr_ok():
    status = HealthStatus(reachable=True, authenticated=True)
    assert "ok=True" in repr(status)


def test_health_status_repr_not_ok_includes_error():
    status = HealthStatus(reachable=False, authenticated=False, error="timeout")
    assert "timeout" in repr(status)


def test_check_health_returns_ok_when_authenticated(mock_client, fast_retry):
    mock_client.is_authenticated.return_value = True
    status = check_health(mock_client, fast_retry)
    assert status.ok is True
    assert status.error is None


def test_check_health_returns_not_ok_when_not_authenticated(mock_client, fast_retry):
    mock_client.is_authenticated.return_value = False
    status = check_health(mock_client, fast_retry)
    assert status.reachable is True
    assert status.authenticated is False


def test_check_health_handles_exception(mock_client, fast_retry):
    mock_client.is_authenticated.side_effect = ConnectionError("refused")
    status = check_health(mock_client, fast_retry)
    assert status.reachable is False
    assert status.authenticated is False
    assert "refused" in (status.error or "")


def test_check_health_uses_default_retry_config(mock_client):
    mock_client.is_authenticated.return_value = True
    status = check_health(mock_client)
    assert status.ok is True
