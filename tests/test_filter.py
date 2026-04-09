"""Tests for vault_sync.filter."""
import pytest

from vault_sync.filter import FilterConfig, apply_filter, parse_patterns


# ---------------------------------------------------------------------------
# FilterConfig.is_allowed
# ---------------------------------------------------------------------------

def test_no_rules_allows_all():
    cfg = FilterConfig()
    assert cfg.is_allowed("SOME_KEY") is True


def test_prefix_filter_blocks_non_matching():
    cfg = FilterConfig(prefix_filter="APP_")
    assert cfg.is_allowed("DB_HOST") is False


def test_prefix_filter_allows_matching():
    cfg = FilterConfig(prefix_filter="APP_")
    assert cfg.is_allowed("APP_SECRET") is True


def test_prefix_filter_is_case_insensitive():
    cfg = FilterConfig(prefix_filter="app_")
    assert cfg.is_allowed("APP_TOKEN") is True


def test_exclude_pattern_blocks_key():
    cfg = FilterConfig(exclude_patterns=["*_PASSWORD"])
    assert cfg.is_allowed("DB_PASSWORD") is False


def test_exclude_pattern_does_not_block_other_keys():
    cfg = FilterConfig(exclude_patterns=["*_PASSWORD"])
    assert cfg.is_allowed("DB_HOST") is True


def test_include_pattern_allows_matching():
    cfg = FilterConfig(include_patterns=["DB_*"])
    assert cfg.is_allowed("DB_HOST") is True


def test_include_pattern_blocks_non_matching():
    cfg = FilterConfig(include_patterns=["DB_*"])
    assert cfg.is_allowed("APP_SECRET") is False


def test_exclude_takes_precedence_over_include():
    cfg = FilterConfig(include_patterns=["DB_*"], exclude_patterns=["DB_PASSWORD"])
    assert cfg.is_allowed("DB_PASSWORD") is False
    assert cfg.is_allowed("DB_HOST") is True


# ---------------------------------------------------------------------------
# apply_filter
# ---------------------------------------------------------------------------

def test_apply_filter_returns_subset():
    secrets = {"APP_KEY": "1", "DB_HOST": "localhost", "APP_TOKEN": "abc"}
    cfg = FilterConfig(prefix_filter="APP_")
    result = apply_filter(secrets, cfg)
    assert result == {"APP_KEY": "1", "APP_TOKEN": "abc"}


def test_apply_filter_empty_secrets():
    result = apply_filter({}, FilterConfig(include_patterns=["*"]))
    assert result == {}


# ---------------------------------------------------------------------------
# parse_patterns
# ---------------------------------------------------------------------------

def test_parse_patterns_comma_separated():
    assert parse_patterns("DB_*,APP_*") == ["DB_*", "APP_*"]


def test_parse_patterns_whitespace_separated():
    assert parse_patterns("DB_* APP_*") == ["DB_*", "APP_*"]


def test_parse_patterns_strips_blanks():
    assert parse_patterns("  DB_*  ,  APP_*  ") == ["DB_*", "APP_*"]
