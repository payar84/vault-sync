"""Tests for vault_sync.tags."""
import pytest

from vault_sync.tags import (
    TagSet,
    filter_by_tags,
    group_by_tag,
    parse_tags,
)


# ---------------------------------------------------------------------------
# TagSet
# ---------------------------------------------------------------------------

def test_tagset_normalises_keys():
    ts = TagSet({"  ENV ": "prod", "Team": "backend"})
    assert "env" in ts.tags
    assert "team" in ts.tags


def test_tagset_has_key_only():
    ts = TagSet({"env": "prod"})
    assert ts.has("env") is True
    assert ts.has("team") is False


def test_tagset_has_key_and_value():
    ts = TagSet({"env": "prod"})
    assert ts.has("env", "prod") is True
    assert ts.has("env", "staging") is False


def test_tagset_to_dict_roundtrip():
    ts = TagSet({"env": "prod", "team": "backend"})
    assert ts.to_dict() == {"env": "prod", "team": "backend"}


def test_tagset_keys():
    ts = TagSet({"env": "prod", "team": "backend"})
    assert ts.keys() == {"env", "team"}


# ---------------------------------------------------------------------------
# parse_tags
# ---------------------------------------------------------------------------

def test_parse_tags_single():
    ts = parse_tags("env=prod")
    assert ts.has("env", "prod")


def test_parse_tags_multiple():
    ts = parse_tags("env=prod,team=backend")
    assert ts.has("env", "prod")
    assert ts.has("team", "backend")


def test_parse_tags_strips_whitespace():
    ts = parse_tags(" env = prod , team = infra ")
    assert ts.has("env", "prod")
    assert ts.has("team", "infra")


def test_parse_tags_invalid_format_raises():
    with pytest.raises(ValueError, match="key=value"):
        parse_tags("envprod")


def test_parse_tags_empty_key_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        parse_tags("=value")


# ---------------------------------------------------------------------------
# filter_by_tags
# ---------------------------------------------------------------------------

_REGISTRY = {
    "secret/app/db": TagSet({"env": "prod", "team": "backend"}),
    "secret/app/cache": TagSet({"env": "prod", "team": "backend"}),
    "secret/app/email": TagSet({"env": "staging", "team": "backend"}),
    "secret/infra/vpn": TagSet({"env": "prod", "team": "infra"}),
}


def test_filter_matches_single_tag():
    result = filter_by_tags(_REGISTRY, TagSet({"env": "prod"}))
    assert "secret/app/db" in result
    assert "secret/app/cache" in result
    assert "secret/infra/vpn" in result
    assert "secret/app/email" not in result


def test_filter_matches_multiple_tags():
    result = filter_by_tags(_REGISTRY, TagSet({"env": "prod", "team": "backend"}))
    assert result == ["secret/app/cache", "secret/app/db"]


def test_filter_no_match_returns_empty():
    result = filter_by_tags(_REGISTRY, TagSet({"env": "dev"}))
    assert result == []


def test_filter_result_is_sorted():
    result = filter_by_tags(_REGISTRY, TagSet({"env": "prod"}))
    assert result == sorted(result)


# ---------------------------------------------------------------------------
# group_by_tag
# ---------------------------------------------------------------------------

def test_group_by_env_tag():
    groups = group_by_tag(_REGISTRY, "env")
    assert "prod" in groups
    assert "staging" in groups
    assert "secret/app/email" in groups["staging"]


def test_group_missing_tag_uses_untagged():
    registry = {
        "secret/a": TagSet({"env": "prod"}),
        "secret/b": TagSet({}),
    }
    groups = group_by_tag(registry, "env")
    assert "__untagged__" in groups
    assert "secret/b" in groups["__untagged__"]


def test_group_values_are_sorted():
    groups = group_by_tag(_REGISTRY, "env")
    for paths in groups.values():
        assert paths == sorted(paths)
