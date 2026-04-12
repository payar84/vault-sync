"""Tests for vault_sync.rate_limiter."""
import time
import pytest
from vault_sync.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    make_rate_limiter,
)


# ---------------------------------------------------------------------------
# RateLimitConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_max_calls():
    with pytest.raises(ValueError, match="max_calls"):
        RateLimitConfig(max_calls=0).validate()


def test_config_rejects_negative_max_calls():
    with pytest.raises(ValueError, match="max_calls"):
        RateLimitConfig(max_calls=-1).validate()


def test_config_rejects_zero_period():
    with pytest.raises(ValueError, match="period_seconds"):
        RateLimitConfig(period_seconds=0).validate()


def test_config_rejects_negative_burst():
    with pytest.raises(ValueError, match="burst"):
        RateLimitConfig(burst=-1).validate()


def test_config_valid_passes():
    cfg = RateLimitConfig(max_calls=5, period_seconds=2.0, burst=2)
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# Token initialisation
# ---------------------------------------------------------------------------

def test_initial_tokens_equal_max_calls():
    rl = make_rate_limiter(max_calls=5)
    assert rl.available_tokens == pytest.approx(5.0, abs=0.1)


def test_initial_tokens_include_burst():
    rl = make_rate_limiter(max_calls=5, burst=3)
    assert rl.available_tokens == pytest.approx(8.0, abs=0.1)


# ---------------------------------------------------------------------------
# acquire – non-blocking
# ---------------------------------------------------------------------------

def test_acquire_succeeds_when_tokens_available():
    rl = make_rate_limiter(max_calls=3)
    assert rl.acquire(block=False) is True


def test_acquire_decrements_token_count():
    rl = make_rate_limiter(max_calls=5)
    rl.acquire(block=False)
    assert rl.available_tokens < 5.0


def test_acquire_fails_when_exhausted_non_blocking():
    rl = make_rate_limiter(max_calls=2, period_seconds=60.0)
    rl.acquire(block=False)
    rl.acquire(block=False)
    # Tokens exhausted; next non-blocking call should fail.
    assert rl.acquire(block=False) is False


def test_multiple_acquires_drain_tokens():
    rl = make_rate_limiter(max_calls=4)
    results = [rl.acquire(block=False) for _ in range(4)]
    assert all(results)
    assert rl.acquire(block=False) is False


# ---------------------------------------------------------------------------
# Token refill
# ---------------------------------------------------------------------------

def test_tokens_refill_over_time():
    rl = make_rate_limiter(max_calls=10, period_seconds=0.1)
    for _ in range(10):
        rl.acquire(block=False)
    # Exhaust tokens, wait for refill
    time.sleep(0.15)
    assert rl.available_tokens > 0


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def test_make_rate_limiter_returns_rate_limiter():
    rl = make_rate_limiter(max_calls=7, period_seconds=2.0)
    assert isinstance(rl, RateLimiter)
    assert rl.config.max_calls == 7
    assert rl.config.period_seconds == 2.0
