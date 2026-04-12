"""Tests for vault_sync.tokenizer."""
from __future__ import annotations

import pytest

from vault_sync.tokenizer import (
    TokenizedPath,
    filter_by_token,
    group_by_parent,
    tokenize_path,
)


# ---------------------------------------------------------------------------
# tokenize_path
# ---------------------------------------------------------------------------

def test_segments_are_split_correctly():
    tp = tokenize_path("secret/prod/db/password")
    assert tp.segments == ["secret", "prod", "db", "password"]


def test_leading_trailing_slashes_are_stripped():
    tp = tokenize_path("/secret/prod/")
    assert tp.segments == ["secret", "prod"]


def test_depth_equals_segment_count():
    tp = tokenize_path("a/b/c")
    assert tp.depth() == 3


def test_leaf_returns_last_segment():
    tp = tokenize_path("secret/prod/db/password")
    assert tp.leaf() == "password"


def test_leaf_is_none_for_empty_path():
    tp = tokenize_path("")
    assert tp.leaf() is None


def test_parent_returns_second_to_last():
    tp = tokenize_path("secret/prod/db/password")
    assert tp.parent() == "secret/prod/db"


def test_parent_is_none_for_single_segment():
    tp = tokenize_path("secret")
    assert tp.parent() is None


def test_tokens_contain_leaf():
    tp = tokenize_path("secret/prod/api/key")
    assert tp.tokens["leaf"] == "key"


def test_tokens_contain_parent():
    tp = tokenize_path("secret/prod/api/key")
    assert tp.tokens["parent"] == "api"


def test_tokens_contain_root():
    tp = tokenize_path("secret/prod/api/key")
    assert tp.tokens["root"] == "secret"


def test_tokens_contain_indexed_segments():
    tp = tokenize_path("a/b/c")
    assert tp.tokens["seg0"] == "a"
    assert tp.tokens["seg1"] == "b"
    assert tp.tokens["seg2"] == "c"


def test_to_dict_contains_all_keys():
    tp = tokenize_path("x/y")
    d = tp.to_dict()
    for key in ("raw", "segments", "tokens", "depth", "leaf", "parent"):
        assert key in d


# ---------------------------------------------------------------------------
# filter_by_token
# ---------------------------------------------------------------------------

def test_filter_returns_matching_paths():
    paths = ["a/prod/db", "a/staging/db", "a/prod/api"]
    result = filter_by_token(paths, "seg1", "prod")
    assert "a/prod/db" in result
    assert "a/prod/api" in result
    assert "a/staging/db" not in result


def test_filter_is_case_insensitive():
    paths = ["a/PROD/db", "a/staging/db"]
    result = filter_by_token(paths, "seg1", "prod")
    assert "a/PROD/db" in result


def test_filter_returns_empty_list_when_no_match():
    paths = ["a/b/c"]
    result = filter_by_token(paths, "leaf", "zzz")
    assert result == []


# ---------------------------------------------------------------------------
# group_by_parent
# ---------------------------------------------------------------------------

def test_group_by_parent_clusters_correctly():
    paths = ["a/b/x", "a/b/y", "a/c/z"]
    groups = group_by_parent(paths)
    assert "a/b" in groups
    assert "a/c" in groups
    assert set(groups["a/b"]) == {"a/b/x", "a/b/y"}


def test_group_by_parent_single_segment_uses_empty_key():
    paths = ["orphan"]
    groups = group_by_parent(paths)
    assert "" in groups
    assert "orphan" in groups[""]
