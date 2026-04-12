"""Tests for vault_sync.resolve."""
from typing import Optional

import pytest

from vault_sync.resolve import ResolveResult, resolve_dict, resolve_references


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STORE = {
    ("secret/db", "password"): "s3cr3t",
    ("secret/app", "api_key"): "abc123",
}


def _fetch(path: str, key: str) -> Optional[str]:
    return _STORE.get((path, key))


# ---------------------------------------------------------------------------
# ResolveResult
# ---------------------------------------------------------------------------

def test_resolve_result_ok_when_no_unresolved():
    r = ResolveResult(value="x", resolved=[("p", "k")], unresolved=[])
    assert r.ok is True


def test_resolve_result_not_ok_when_unresolved():
    r = ResolveResult(value="x", resolved=[], unresolved=[("p", "k")])
    assert r.ok is False


# ---------------------------------------------------------------------------
# resolve_references
# ---------------------------------------------------------------------------

def test_single_reference_is_replaced():
    result = resolve_references("{{secret/db:password}}", _fetch)
    assert result.value == "s3cr3t"
    assert result.ok


def test_multiple_references_are_replaced():
    result = resolve_references(
        "{{secret/db:password}}:{{secret/app:api_key}}", _fetch
    )
    assert result.value == "s3cr3t:abc123"
    assert len(result.resolved) == 2


def test_missing_reference_is_left_verbatim():
    result = resolve_references("{{secret/db:missing}}", _fetch)
    assert result.value == "{{secret/db:missing}}"
    assert not result.ok
    assert result.unresolved == [("secret/db", "missing")]


def test_plain_value_is_unchanged():
    result = resolve_references("no-references-here", _fetch)
    assert result.value == "no-references-here"
    assert result.ok
    assert result.resolved == []


def test_partial_resolution_tracks_both_lists():
    result = resolve_references(
        "{{secret/db:password}} and {{secret/db:missing}}", _fetch
    )
    assert "s3cr3t" in result.value
    assert len(result.resolved) == 1
    assert len(result.unresolved) == 1


def test_whitespace_around_path_and_key_is_stripped():
    result = resolve_references("{{ secret/db : password }}", _fetch)
    assert result.value == "s3cr3t"


# ---------------------------------------------------------------------------
# resolve_dict
# ---------------------------------------------------------------------------

def test_resolve_dict_updates_values():
    secrets = {"DB_PASS": "{{secret/db:password}}", "PLAIN": "hello"}
    out, unresolved = resolve_dict(secrets, _fetch)
    assert out["DB_PASS"] == "s3cr3t"
    assert out["PLAIN"] == "hello"
    assert unresolved == []


def test_resolve_dict_reports_unresolved():
    secrets = {"X": "{{secret/db:nope}}"}
    out, unresolved = resolve_dict(secrets, _fetch)
    assert out["X"] == "{{secret/db:nope}}"
    assert unresolved == [("X", "secret/db", "nope")]


def test_resolve_dict_empty_input():
    out, unresolved = resolve_dict({}, _fetch)
    assert out == {}
    assert unresolved == []
