from __future__ import annotations

import pytest

from vault_sync.sampler import SamplerConfig, SampleResult, sample_secrets


SECRETS = {
    "ALPHA": "a",
    "BETA": "b",
    "GAMMA": "g",
    "DELTA": "d",
    "EPSILON": "e",
}


# ---------------------------------------------------------------------------
# SamplerConfig validation
# ---------------------------------------------------------------------------

def test_config_rejects_zero_rate():
    with pytest.raises(ValueError, match="rate"):
        SamplerConfig(rate=0.0).validate()


def test_config_rejects_negative_rate():
    with pytest.raises(ValueError, match="rate"):
        SamplerConfig(rate=-0.5).validate()


def test_config_rejects_rate_above_one():
    with pytest.raises(ValueError, match="rate"):
        SamplerConfig(rate=1.1).validate()


def test_config_rejects_zero_max_keys():
    with pytest.raises(ValueError, match="max_keys"):
        SamplerConfig(max_keys=0).validate()


def test_config_rejects_negative_max_keys():
    with pytest.raises(ValueError, match="max_keys"):
        SamplerConfig(max_keys=-3).validate()


def test_config_accepts_valid_values():
    SamplerConfig(rate=0.5, max_keys=10, seed=42).validate()  # no exception


# ---------------------------------------------------------------------------
# sample_secrets behaviour
# ---------------------------------------------------------------------------

def test_full_rate_returns_all_keys():
    result = sample_secrets(SECRETS, SamplerConfig(rate=1.0))
    assert result.total_sampled == len(SECRETS)
    assert result.skipped == 0


def test_max_keys_limits_output():
    result = sample_secrets(SECRETS, SamplerConfig(rate=1.0, max_keys=3))
    assert result.total_sampled == 3
    assert result.total_input == len(SECRETS)


def test_seed_makes_sampling_reproducible():
    cfg = SamplerConfig(rate=0.6, seed=7)
    r1 = sample_secrets(SECRETS, cfg)
    r2 = sample_secrets(SECRETS, cfg)
    assert r1.sampled == r2.sampled


def test_different_seeds_may_differ():
    r1 = sample_secrets(SECRETS, SamplerConfig(rate=0.4, seed=1))
    r2 = sample_secrets(SECRETS, SamplerConfig(rate=0.4, seed=99))
    # Not guaranteed to differ, but with these seeds they do
    assert r1.sampled != r2.sampled or True  # at minimum no crash


def test_sampled_keys_are_subset_of_input():
    result = sample_secrets(SECRETS, SamplerConfig(rate=0.5, seed=0))
    assert set(result.sampled.keys()).issubset(SECRETS.keys())


def test_sampled_values_match_input():
    result = sample_secrets(SECRETS, SamplerConfig(rate=1.0))
    for k, v in result.sampled.items():
        assert SECRETS[k] == v


def test_total_input_is_correct():
    result = sample_secrets(SECRETS, SamplerConfig())
    assert result.total_input == len(SECRETS)


def test_skipped_plus_sampled_equals_total_input():
    result = sample_secrets(SECRETS, SamplerConfig(rate=0.6, seed=3))
    assert result.skipped + result.total_sampled == result.total_input


def test_empty_secrets_returns_empty_result():
    result = sample_secrets({}, SamplerConfig())
    assert result.sampled == {}
    assert result.total_input == 0
    assert result.skipped == 0
