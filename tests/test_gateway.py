"""Tests for vault_sync.gateway"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from vault_sync.gateway import Gateway, GatewayConfig, GatewayResult
from vault_sync.rate_limiter import RateLimitConfig
from vault_sync.circuit_breaker import CircuitBreakerConfig, CircuitState
from vault_sync.deadline import DeadlineConfig


@pytest.fixture()
def cfg() -> GatewayConfig:
    return GatewayConfig(
        rate_limit=RateLimitConfig(max_calls=100, period=1.0, burst=10),
        circuit_breaker=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30, success_threshold=2),
        deadline=DeadlineConfig(max_duration=60.0, warn_at=0.8),
    )


@pytest.fixture()
def mock_client():
    client = MagicMock()
    client.read_secret.return_value = {"KEY": "value"}
    return client


@pytest.fixture()
def gateway(cfg, mock_client) -> Gateway:
    return Gateway(cfg, mock_client)


def test_gateway_result_ok_is_success():
    r = GatewayResult.ok({"A": "1"})
    assert r.success is True
    assert r.value == {"A": "1"}


def test_gateway_result_fail_is_not_success():
    r = GatewayResult.fail("circuit open")
    assert r.success is False
    assert r.value is None
    assert r.reason == "circuit open"


def test_successful_read_returns_ok(gateway, mock_client):
    result = gateway.read_secret("secret/app")
    assert result.success is True
    assert result.value == {"KEY": "value"}
    mock_client.read_secret.assert_called_once_with("secret/app")


def test_client_exception_returns_fail(cfg, mock_client):
    mock_client.read_secret.side_effect = RuntimeError("connection refused")
    gw = Gateway(cfg, mock_client)
    result = gw.read_secret("secret/app")
    assert result.success is False
    assert "connection refused" in result.reason


def test_circuit_open_returns_fail(cfg, mock_client):
    gw = Gateway(cfg, mock_client)
    # Force circuit open by tripping enough failures
    for _ in range(cfg.circuit_breaker.failure_threshold):
        gw._breaker.record_failure()
    assert gw._breaker.state == CircuitState.OPEN
    result = gw.read_secret("secret/app")
    assert result.success is False
    assert "circuit open" in result.reason


def test_expired_deadline_returns_fail(mock_client):
    cfg = GatewayConfig(
        rate_limit=RateLimitConfig(max_calls=100, period=1.0, burst=10),
        circuit_breaker=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30, success_threshold=2),
        deadline=DeadlineConfig(max_duration=0.000001, warn_at=0.5),
    )
    import time
    time.sleep(0.01)  # ensure deadline is exceeded
    gw = Gateway(cfg, mock_client)
    result = gw.read_secret("secret/app")
    assert result.success is False
    assert "deadline" in result.reason


def test_breaker_records_success_on_ok_read(gateway, mock_client):
    initial_failures = gateway._breaker._failure_count
    gateway.read_secret("secret/app")
    # success should not increment failures
    assert gateway._breaker._failure_count == initial_failures


def test_breaker_records_failure_on_exception(cfg, mock_client):
    mock_client.read_secret.side_effect = RuntimeError("boom")
    gw = Gateway(cfg, mock_client)
    gw.read_secret("secret/app")
    assert gw._breaker._failure_count == 1
