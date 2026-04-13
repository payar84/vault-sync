"""Tests for vault_sync.pipeline."""
from __future__ import annotations

import pytest

from vault_sync.pipeline import PipelineConfig, PipelineResult, run_pipeline
from vault_sync.filter import FilterConfig
from vault_sync.transform import strip_whitespace, to_uppercase_value, mask_sensitive
from vault_sync.alias import AliasMap


SECRETS = {
    "db_password": "  secret  ",
    "api_key": "abc123",
    "app_debug": "true",
}


def test_empty_pipeline_returns_all_secrets():
    result = run_pipeline(SECRETS, PipelineConfig())
    assert result.secrets == SECRETS
    assert result.dropped == []
    assert result.renamed == {}


def test_filter_drops_excluded_keys():
    cfg = PipelineConfig(
        filter_config=FilterConfig(exclude_patterns=["debug"])
    )
    result = run_pipeline(SECRETS, cfg)
    assert "app_debug" not in result.secrets
    assert "app_debug" in result.dropped


def test_filter_keeps_included_prefix():
    cfg = PipelineConfig(
        filter_config=FilterConfig(include_prefixes=["db_"])
    )
    result = run_pipeline(SECRETS, cfg)
    assert list(result.secrets.keys()) == ["db_password"]
    assert len(result.dropped) == 2


def test_transform_strips_whitespace():
    cfg = PipelineConfig(transforms=[strip_whitespace])
    result = run_pipeline(SECRETS, cfg)
    assert result.secrets["db_password"] == "secret"


def test_transform_uppercases_values():
    cfg = PipelineConfig(transforms=[to_uppercase_value])
    result = run_pipeline(SECRETS, cfg)
    assert result.secrets["api_key"] == "ABC123"


def test_transform_masks_sensitive_keys():
    cfg = PipelineConfig(transforms=[mask_sensitive])
    result = run_pipeline(SECRETS, cfg)
    assert result.secrets["db_password"] == "***"
    assert result.secrets["api_key"] == "***"


def test_alias_renames_key():
    alias_map = AliasMap(aliases={"db_password": "DATABASE_PASSWORD"})
    cfg = PipelineConfig(alias_map=alias_map)
    result = run_pipeline(SECRETS, cfg)
    assert "DATABASE_PASSWORD" in result.secrets
    assert "db_password" not in result.secrets
    assert result.renamed["db_password"] == "DATABASE_PASSWORD"


def test_alias_leaves_unaliased_keys_uppercased():
    alias_map = AliasMap(aliases={})
    cfg = PipelineConfig(alias_map=alias_map)
    result = run_pipeline(SECRETS, cfg)
    # AliasMap.resolve uppercases by default
    assert "DB_PASSWORD" in result.secrets


def test_pipeline_result_total():
    result = PipelineResult(secrets={"A": "1", "B": "2"})
    assert result.total == 2


def test_pipeline_result_repr():
    result = PipelineResult(secrets={"A": "1"}, dropped=["X"], renamed={"old": "NEW"})
    r = repr(result)
    assert "total=1" in r
    assert "dropped=1" in r
    assert "renamed=1" in r


def test_filter_then_transform_order():
    """Filter runs before transform — dropped keys are not transformed."""
    cfg = PipelineConfig(
        filter_config=FilterConfig(exclude_patterns=["debug"]),
        transforms=[mask_sensitive],
    )
    result = run_pipeline(SECRETS, cfg)
    assert "app_debug" not in result.secrets
    assert result.secrets["db_password"] == "***"
