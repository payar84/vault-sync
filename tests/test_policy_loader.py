"""Tests for vault_sync.policy_loader module."""
import json
import pytest
from pathlib import Path

from vault_sync.policy_loader import load_policy_file, load_policy_or_default
from vault_sync.policy import Policy


@pytest.fixture()
def json_policy_file(tmp_path: Path) -> Path:
    rules = [
        {"path": "secret/app", "allowed_keys": ["DB_*"]},
        {"path": "secret/forbidden", "deny": True},
    ]
    p = tmp_path / "policy.json"
    p.write_text(json.dumps(rules))
    return p


def test_load_json_policy_returns_policy(json_policy_file):
    policy = load_policy_file(str(json_policy_file))
    assert isinstance(policy, Policy)
    assert len(policy.rules) == 2


def test_load_json_policy_rule_attributes(json_policy_file):
    policy = load_policy_file(str(json_policy_file))
    first = policy.rules[0]
    assert first.path_pattern == "secret/app"
    assert first.allowed_keys == ["DB_*"]
    assert not first.deny


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_policy_file(str(tmp_path / "missing.json"))


def test_load_unsupported_format_raises(tmp_path):
    p = tmp_path / "policy.toml"
    p.write_text("[[rules]]\n")
    with pytest.raises(ValueError, match="Unsupported"):
        load_policy_file(str(p))


def test_load_non_list_json_raises(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({"rules": []}))
    with pytest.raises(ValueError, match="top-level list"):
        load_policy_file(str(p))


def test_load_policy_or_default_returns_empty_policy_when_none():
    policy = load_policy_or_default(None)
    assert isinstance(policy, Policy)
    assert policy.rules == []


def test_load_policy_or_default_loads_file(json_policy_file):
    policy = load_policy_or_default(str(json_policy_file))
    assert len(policy.rules) == 2
