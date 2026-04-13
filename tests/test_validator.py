"""Tests for vault_sync.validator."""
import pytest
from vault_sync.validator import (
    ValidationRule,
    ValidationResult,
    validate_secrets,
    parse_rules,
)


# ---------------------------------------------------------------------------
# ValidationRule.validate
# ---------------------------------------------------------------------------

def test_required_rule_errors_when_missing():
    rule = ValidationRule(key="API_KEY", required=True)
    errors = rule.validate(None)
    assert len(errors) == 1
    assert "required" in errors[0]


def test_required_rule_errors_on_empty_string():
    rule = ValidationRule(key="API_KEY", required=True)
    errors = rule.validate("")
    assert len(errors) == 1


def test_optional_rule_passes_when_missing():
    rule = ValidationRule(key="OPTIONAL_KEY", required=False)
    errors = rule.validate(None)
    assert errors == []


def test_min_length_violation():
    rule = ValidationRule(key="TOKEN", min_length=8)
    errors = rule.validate("short")
    assert any("minimum" in e for e in errors)


def test_min_length_passes():
    rule = ValidationRule(key="TOKEN", min_length=4)
    errors = rule.validate("longvalue")
    assert errors == []


def test_max_length_violation():
    rule = ValidationRule(key="NAME", max_length=5)
    errors = rule.validate("toolongvalue")
    assert any("exceeds" in e for e in errors)


def test_max_length_passes():
    rule = ValidationRule(key="NAME", max_length=20)
    errors = rule.validate("ok")
    assert errors == []


def test_pattern_match_passes():
    rule = ValidationRule(key="PORT", pattern=r"\d+")
    errors = rule.validate("8080")
    assert errors == []


def test_pattern_mismatch_errors():
    rule = ValidationRule(key="PORT", pattern=r"\d+")
    errors = rule.validate("not-a-number")
    assert any("pattern" in e for e in errors)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_result_ok_when_no_errors():
    result = ValidationResult()
    assert result.ok is True


def test_result_not_ok_when_errors():
    result = ValidationResult(errors=["something wrong"])
    assert result.ok is False


# ---------------------------------------------------------------------------
# validate_secrets
# ---------------------------------------------------------------------------

def test_validate_secrets_passes_all_valid():
    secrets = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    rules = [
        ValidationRule(key="DB_HOST"),
        ValidationRule(key="DB_PORT", pattern=r"\d+"),
    ]
    result = validate_secrets(secrets, rules)
    assert result.ok


def test_validate_secrets_collects_multiple_errors():
    secrets = {"DB_HOST": ""}
    rules = [
        ValidationRule(key="DB_HOST"),
        ValidationRule(key="DB_PORT"),
    ]
    result = validate_secrets(secrets, rules)
    assert not result.ok
    assert len(result.errors) == 2


# ---------------------------------------------------------------------------
# parse_rules
# ---------------------------------------------------------------------------

def test_parse_rules_builds_correct_objects():
    raw = [
        {"key": "SECRET", "required": True, "min_length": 10, "pattern": r"[A-Z]+"},
    ]
    rules = parse_rules(raw)
    assert len(rules) == 1
    r = rules[0]
    assert r.key == "SECRET"
    assert r.required is True
    assert r.min_length == 10
    assert r.pattern == r"[A-Z]+"


def test_parse_rules_defaults_required_to_true():
    raw = [{"key": "MY_KEY"}]
    rules = parse_rules(raw)
    assert rules[0].required is True
