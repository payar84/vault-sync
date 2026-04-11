"""Tests for vault_sync.merge."""
import pytest
from vault_sync.merge import MergeStrategy, MergeResult, merge_secrets, parse_strategy


VAULT = {"DB_HOST": "vault-host", "DB_PORT": "5432", "NEW_KEY": "new-val"}
LOCAL = {"DB_HOST": "local-host", "DB_PORT": "5432", "LOCAL_ONLY": "keep-me"}


# --- merge_secrets ---

def test_vault_wins_overwrites_changed_keys():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.VAULT_WINS)
    assert result.merged["DB_HOST"] == "vault-host"


def test_vault_wins_adds_new_keys():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.VAULT_WINS)
    assert result.merged["NEW_KEY"] == "new-val"
    assert result.added == 1


def test_vault_wins_preserves_identical_keys():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.VAULT_WINS)
    assert result.preserved == 1  # DB_PORT unchanged
    assert result.overwritten == 1  # DB_HOST changed


def test_vault_wins_keeps_local_only_keys():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.VAULT_WINS)
    assert result.merged["LOCAL_ONLY"] == "keep-me"


def test_local_wins_does_not_overwrite_existing():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.LOCAL_WINS)
    assert result.merged["DB_HOST"] == "local-host"
    assert result.overwritten == 0


def test_local_wins_still_adds_new_keys():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.LOCAL_WINS)
    assert result.merged["NEW_KEY"] == "new-val"
    assert result.added == 1


def test_new_only_does_not_overwrite_existing():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.NEW_ONLY)
    assert result.merged["DB_HOST"] == "local-host"
    assert result.overwritten == 0


def test_new_only_adds_absent_keys():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.NEW_ONLY)
    assert result.merged["NEW_KEY"] == "new-val"
    assert result.added == 1


def test_empty_local_all_added():
    result = merge_secrets(VAULT, {}, strategy=MergeStrategy.VAULT_WINS)
    assert result.added == len(VAULT)
    assert result.overwritten == 0
    assert result.preserved == 0


def test_total_equals_sum_of_parts():
    result = merge_secrets(VAULT, LOCAL, strategy=MergeStrategy.VAULT_WINS)
    assert result.total == result.added + result.overwritten + result.preserved


def test_merge_result_repr_contains_counts():
    result = MergeResult(merged={}, overwritten=2, preserved=1, added=3)
    r = repr(result)
    assert "added=3" in r
    assert "overwritten=2" in r
    assert "preserved=1" in r


# --- parse_strategy ---

def test_parse_strategy_vault_wins():
    assert parse_strategy("vault_wins") == MergeStrategy.VAULT_WINS


def test_parse_strategy_local_wins():
    assert parse_strategy("local_wins") == MergeStrategy.LOCAL_WINS


def test_parse_strategy_none_defaults_to_vault_wins():
    assert parse_strategy(None) == MergeStrategy.VAULT_WINS


def test_parse_strategy_case_insensitive():
    assert parse_strategy("NEW_ONLY") == MergeStrategy.NEW_ONLY


def test_parse_strategy_unknown_raises():
    with pytest.raises(ValueError, match="Unknown merge strategy"):
        parse_strategy("overwrite_everything")
