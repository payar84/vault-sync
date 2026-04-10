"""Tests for vault_sync.policy module."""
import pytest
from vault_sync.policy import Policy, PolicyRule, parse_policy, apply_policy


# ---------------------------------------------------------------------------
# PolicyRule
# ---------------------------------------------------------------------------

def test_rule_matches_exact_path():
    rule = PolicyRule(path_pattern="secret/app")
    assert rule.matches_path("secret/app")


def test_rule_matches_wildcard_path():
    rule = PolicyRule(path_pattern="secret/*")
    assert rule.matches_path("secret/db")
    assert not rule.matches_path("other/db")


def test_rule_strips_leading_slashes():
    rule = PolicyRule(path_pattern="/secret/app/")
    assert rule.matches_path("/secret/app")


def test_rule_allows_all_keys_when_none():
    rule = PolicyRule(path_pattern="secret/app", allowed_keys=None)
    assert rule.allows_key("DB_PASSWORD")
    assert rule.allows_key("anything")


def test_rule_restricts_to_allowed_keys():
    rule = PolicyRule(path_pattern="secret/app", allowed_keys=["DB_*"])
    assert rule.allows_key("DB_PASSWORD")
    assert not rule.allows_key("API_KEY")


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

def test_policy_allows_path_with_no_rules():
    policy = Policy()
    assert policy.is_path_allowed("secret/anything")


def test_policy_deny_rule_blocks_path():
    policy = Policy(rules=[PolicyRule(path_pattern="secret/forbidden", deny=True)])
    assert not policy.is_path_allowed("secret/forbidden")
    assert policy.is_path_allowed("secret/allowed")


def test_policy_last_matching_rule_wins():
    policy = Policy(rules=[
        PolicyRule(path_pattern="secret/*", deny=True),
        PolicyRule(path_pattern="secret/app", deny=False),
    ])
    assert policy.is_path_allowed("secret/app")
    assert not policy.is_path_allowed("secret/other")


def test_policy_key_allowed_respects_allowed_keys():
    policy = Policy(rules=[
        PolicyRule(path_pattern="secret/app", allowed_keys=["DB_*"])
    ])
    assert policy.is_key_allowed("secret/app", "DB_HOST")
    assert not policy.is_key_allowed("secret/app", "API_TOKEN")


# ---------------------------------------------------------------------------
# parse_policy
# ---------------------------------------------------------------------------

def test_parse_policy_from_dicts():
    raw = [{"path": "secret/*", "deny": False, "allowed_keys": ["DB_*"]}]
    policy = parse_policy(raw)
    assert len(policy.rules) == 1
    assert policy.rules[0].path_pattern == "secret/*"


# ---------------------------------------------------------------------------
# apply_policy
# ---------------------------------------------------------------------------

def test_apply_policy_filters_keys():
    policy = Policy(rules=[PolicyRule(path_pattern="secret/app", allowed_keys=["DB_HOST"])])
    secrets = {"DB_HOST": "localhost", "API_KEY": "abc"}
    result = apply_policy(policy, "secret/app", secrets)
    assert result == {"DB_HOST": "localhost"}


def test_apply_policy_blocks_entire_path():
    policy = Policy(rules=[PolicyRule(path_pattern="secret/forbidden", deny=True)])
    secrets = {"KEY": "value"}
    assert apply_policy(policy, "secret/forbidden", secrets) == {}


def test_apply_policy_allows_all_when_no_rules():
    policy = Policy()
    secrets = {"A": "1", "B": "2"}
    assert apply_policy(policy, "any/path", secrets) == secrets
