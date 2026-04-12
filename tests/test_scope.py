"""Tests for vault_sync.scope."""
from __future__ import annotations

import pytest

from vault_sync.scope import ScopeConfig, parse_scope


# ---------------------------------------------------------------------------
# ScopeConfig.is_in_scope
# ---------------------------------------------------------------------------

def test_no_rules_allows_all_paths():
    scope = parse_scope()
    assert scope.is_in_scope("secret/app/prod/db") is True


def test_include_pattern_allows_matching_path():
    scope = parse_scope(include=["secret/app/*"])
    assert scope.is_in_scope("secret/app/prod") is True


def test_include_pattern_blocks_non_matching_path():
    scope = parse_scope(include=["secret/app/*"])
    assert scope.is_in_scope("secret/infra/tls") is False


def test_exclude_pattern_removes_matching_path():
    scope = parse_scope(exclude=["secret/infra/*"])
    assert scope.is_in_scope("secret/infra/tls") is False


def test_exclude_does_not_affect_non_matching_path():
    scope = parse_scope(exclude=["secret/infra/*"])
    assert scope.is_in_scope("secret/app/prod") is True


def test_exclude_takes_priority_over_include():
    scope = parse_scope(include=["secret/*"], exclude=["secret/infra/*"])
    assert scope.is_in_scope("secret/infra/tls") is False
    assert scope.is_in_scope("secret/app/prod") is True


def test_leading_slashes_are_stripped():
    scope = parse_scope(include=["secret/app/*"])
    assert scope.is_in_scope("/secret/app/prod") is True


def test_multiple_include_patterns_are_unioned():
    scope = parse_scope(include=["secret/app/*", "secret/shared/*"])
    assert scope.is_in_scope("secret/app/db") is True
    assert scope.is_in_scope("secret/shared/oauth") is True
    assert scope.is_in_scope("secret/infra/tls") is False


# ---------------------------------------------------------------------------
# ScopeConfig.filter_paths
# ---------------------------------------------------------------------------

def test_filter_paths_returns_only_in_scope():
    scope = parse_scope(include=["secret/app/*"])
    paths = ["secret/app/db", "secret/infra/tls", "secret/app/api"]
    result = scope.filter_paths(paths)
    assert result == ["secret/app/db", "secret/app/api"]


def test_filter_paths_empty_list_returns_empty():
    scope = parse_scope(include=["secret/app/*"])
    assert scope.filter_paths([]) == []


def test_filter_paths_no_rules_returns_all():
    scope = parse_scope()
    paths = ["a", "b", "c"]
    assert scope.filter_paths(paths) == paths


# ---------------------------------------------------------------------------
# parse_scope helper
# ---------------------------------------------------------------------------

def test_parse_scope_returns_scope_config():
    scope = parse_scope(include=["secret/*"], exclude=["secret/tmp/*"])
    assert isinstance(scope, ScopeConfig)
    assert scope.include == ["secret/*"]
    assert scope.exclude == ["secret/tmp/*"]


def test_parse_scope_defaults_to_empty_lists():
    scope = parse_scope()
    assert scope.include == []
    assert scope.exclude == []
