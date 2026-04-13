import time
import pytest
from vault_sync.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


@pytest.fixture
def config() -> CircuitBreakerConfig:
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1.0,
        success_threshold=2,
    )


@pytest.fixture
def breaker(config: CircuitBreakerConfig) -> CircuitBreaker:
    return CircuitBreaker(config=config)


def test_config_rejects_zero_failure_threshold():
    with pytest.raises(ValueError, match="failure_threshold"):
        CircuitBreakerConfig(failure_threshold=0).validate()


def test_config_rejects_zero_recovery_timeout():
    with pytest.raises(ValueError, match="recovery_timeout"):
        CircuitBreakerConfig(recovery_timeout=0).validate()


def test_config_rejects_zero_success_threshold():
    with pytest.raises(ValueError, match="success_threshold"):
        CircuitBreakerConfig(success_threshold=0).validate()


def test_initial_state_is_closed(breaker):
    assert breaker.state == CircuitState.CLOSED


def test_successful_call_returns_value(breaker):
    result = breaker.call(lambda: 42)
    assert result == 42


def test_failures_below_threshold_stay_closed(breaker):
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert breaker.state == CircuitState.CLOSED


def test_failures_at_threshold_open_circuit(breaker):
    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert breaker.state == CircuitState.OPEN


def test_open_circuit_blocks_calls(breaker):
    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    with pytest.raises(RuntimeError, match="OPEN"):
        breaker.call(lambda: 1)


def test_circuit_transitions_to_half_open_after_timeout(breaker):
    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    breaker._opened_at = time.monotonic() - 2.0
    assert breaker.state == CircuitState.HALF_OPEN


def test_half_open_success_closes_circuit(breaker):
    for _ in range(3):
 pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    breaker._opened_at = time.monotonic() - 2.0
    breaker.call(lambda: None)
    breaker.call(lambda: None)
    assert breaker.state == CircuitState.CLOSED


def test_half_open_failure_reopens_circuit(breaker):
    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    breaker._opened_at = time.monotonic() - 2.0
    _ = breaker.state  # trigger transition
    with pytest.raises(ValueError):
        breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    assert breaker.state == CircuitState.OPEN


def test_reset_restores_closed_state(breaker):
    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("boom")))
    breaker.reset()
    assert breaker.state == CircuitState.CLOSED
    assert breaker._failure_count == 0


def test_repr_contains_state_and_failures(breaker):
    text = repr(breaker)
    assert "closed" in text
    assert "failures" in text
