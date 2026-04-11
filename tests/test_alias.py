"""Tests for vault_sync.alias."""
import json
import pytest
from pathlib import Path

from vault_sync.alias import AliasMap, apply_aliases, load_alias_file


# ---------------------------------------------------------------------------
# AliasMap unit tests
# ---------------------------------------------------------------------------

def test_resolve_returns_alias_when_present():
    am = AliasMap({"db_password": "DATABASE_PASSWORD"})
    assert am.resolve("db_password") == "DATABASE_PASSWORD"


def test_resolve_returns_uppercased_key_when_no_alias():
    am = AliasMap({})
    assert am.resolve("my_key") == "MY_KEY"


def test_aliases_are_normalised_to_uppercase():
    am = AliasMap({"api_token": "service_api_key"})
    assert am.resolve("API_TOKEN") == "SERVICE_API_KEY"


def test_has_alias_true_for_registered_key():
    am = AliasMap({"secret_key": "APP_SECRET"})
    assert am.has_alias("secret_key") is True


def test_has_alias_false_for_unknown_key():
    am = AliasMap({"secret_key": "APP_SECRET"})
    assert am.has_alias("other_key") is False


def test_has_alias_is_case_insensitive():
    am = AliasMap({"MY_KEY": "RENAMED"})
    assert am.has_alias("my_key") is True


def test_all_aliases_returns_copy():
    am = AliasMap({"a": "b"})
    copy = am.all_aliases()
    copy["extra"] = "x"
    assert "EXTRA" not in am.all_aliases()


def test_to_dict_matches_all_aliases():
    am = AliasMap({"x": "y"})
    assert am.to_dict() == am.all_aliases()


# ---------------------------------------------------------------------------
# apply_aliases
# ---------------------------------------------------------------------------

def test_apply_aliases_renames_keys():
    secrets = {"DB_PASSWORD": "secret", "API_TOKEN": "tok"}
    am = AliasMap({"DB_PASSWORD": "DATABASE_PASSWORD"})
    result = apply_aliases(secrets, am)
    assert "DATABASE_PASSWORD" in result
    assert result["DATABASE_PASSWORD"] == "secret"


def test_apply_aliases_leaves_unaliased_keys_uppercased():
    secrets = {"plain_key": "val"}
    am = AliasMap({})
    result = apply_aliases(secrets, am)
    assert result.get("PLAIN_KEY") == "val"


# ---------------------------------------------------------------------------
# load_alias_file
# ---------------------------------------------------------------------------

def test_load_alias_file_returns_alias_map(tmp_path: Path):
    f = tmp_path / "aliases.json"
    f.write_text(json.dumps({"db_pass": "DATABASE_PASSWORD"}))
    am = load_alias_file(f)
    assert am.resolve("db_pass") == "DATABASE_PASSWORD"


def test_load_alias_file_raises_for_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_alias_file(tmp_path / "nope.json")


def test_load_alias_file_raises_for_invalid_json(tmp_path: Path):
    f = tmp_path / "bad.json"
    f.write_text("not json")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_alias_file(f)


def test_load_alias_file_raises_for_non_object(tmp_path: Path):
    f = tmp_path / "list.json"
    f.write_text(json.dumps(["a", "b"]))
    with pytest.raises(ValueError, match="JSON object"):
        load_alias_file(f)


def test_load_alias_file_raises_for_non_string_values(tmp_path: Path):
    f = tmp_path / "bad_vals.json"
    f.write_text(json.dumps({"key": 123}))
    with pytest.raises(ValueError, match="strings"):
        load_alias_file(f)
