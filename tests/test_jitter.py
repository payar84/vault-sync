"""Tests for vault_sync.jitter."""
from __future__ import annotations

import pytest

from vault_sync.jitter import (
    JitterConfig,
    JitterResult,
    JitterStrategy,
    apply_jitter,
)


# ---------------------------------------------------------------------------
# JitterConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_negative_min_delay():
    with pytest.raises(ValueError, match="min_delay"):
        JitterConfig(min_delay=-1.0, max_delay=10.0)


def test_config_rejects_zero_max_delay():
    with pytest.raises(ValueError, match="max_delay"):
        JitterConfig(min_delay=0.0, max_delay=0.0)


def test_config_rejects_min_equal_to_max():
    with pytest.raises(ValueError, match="min_delay must be less than max_delay"):
        JitterConfig(min_delay=5.0, max_delay=5.0)


def test_config_rejects_min_greater_than_max():
    with pytest.raises(ValueError, match="min_delay must be less than max_delay"):
        JitterConfig(min_delay=10.0, max_delay=5.0)


def test_config_accepts_valid_values():
    cfg = JitterConfig(strategy=JitterStrategy.EQUAL, min_delay=0.1, max_delay=20.0)
    assert cfg.min_delay == 0.1
    assert cfg.max_delay == 20.0


# ---------------------------------------------------------------------------
# NONE strategy
# ---------------------------------------------------------------------------

def test_none_strategy_returns_base_delay():
    cfg = JitterConfig(strategy=JitterStrategy.NONE, seed=42)
    result = apply_jitter(2.5, cfg)
    assert result.jittered_delay == 2.5


# ---------------------------------------------------------------------------
# FULL strategy
# ---------------------------------------------------------------------------

def test_full_strategy_result_within_bounds():
    cfg = JitterConfig(strategy=JitterStrategy.FULL, min_delay=0.0, max_delay=10.0, seed=0)
    for _ in range(20):
        r = apply_jitter(5.0, cfg)
        assert cfg.min_delay <= r.jittered_delay <= cfg.max_delay


# ---------------------------------------------------------------------------
# EQUAL strategy
# ---------------------------------------------------------------------------

def test_equal_strategy_result_within_bounds():
    cfg = JitterConfig(strategy=JitterStrategy.EQUAL, min_delay=0.0, max_delay=10.0, seed=1)
    for _ in range(20):
        r = apply_jitter(4.0, cfg)
        assert cfg.min_delay <= r.jittered_delay <= cfg.max_delay


# ---------------------------------------------------------------------------
# DECORRELATED strategy
# ---------------------------------------------------------------------------

def test_decorrelated_strategy_result_within_bounds():
    cfg = JitterConfig(strategy=JitterStrategy.DECORRELATED, min_delay=0.0, max_delay=30.0, seed=7)
    for _ in range(20):
        r = apply_jitter(3.0, cfg)
        assert cfg.min_delay <= r.jittered_delay <= cfg.max_delay


# ---------------------------------------------------------------------------
# JitterResult
# ---------------------------------------------------------------------------

def test_result_stores_base_delay():
    cfg = JitterConfig(strategy=JitterStrategy.NONE, seed=0)
    r = apply_jitter(1.5, cfg)
    assert r.base_delay == 1.5


def test_result_stores_strategy():
    cfg = JitterConfig(strategy=JitterStrategy.FULL, seed=0)
    r = apply_jitter(1.0, cfg)
    assert r.strategy == JitterStrategy.FULL


def test_result_repr_contains_strategy():
    cfg = JitterConfig(strategy=JitterStrategy.FULL, seed=0)
    r = apply_jitter(1.0, cfg)
    assert "full" in repr(r)


def test_seeded_config_is_reproducible():
    cfg1 = JitterConfig(strategy=JitterStrategy.FULL, seed=99)
    cfg2 = JitterConfig(strategy=JitterStrategy.FULL, seed=99)
    r1 = apply_jitter(5.0, cfg1)
    r2 = apply_jitter(5.0, cfg2)
    assert r1.jittered_delay == r2.jittered_delay
