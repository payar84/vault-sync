"""Tests for vault_sync.redactor."""

import pytest
from vault_sync.redactor import (
    Redactor,
    build_redactor,
    DEFAULT_SENSITIVE_PATTERNS,
    REDACTED_PLACEHOLDER,
)


@pytest.fixture
def redactor() -> Redactor:
    return Redactor()


def test_password_key_is_sensitive(redactor):
    assert redactor.is_sensitive("PASSWORD") is True


def test_token_key_is_sensitive(redactor):
    assert redactor.is_sensitive("AUTH_TOKEN") is True


def test_api_key_is_sensitive(redactor):
    assert redactor.is_sensitive("STRIPE_API_KEY") is True


def test_plain_key_is_not_sensitive(redactor):
    assert redactor.is_sensitive("DATABASE_HOST") is False


def test_redact_replaces_sensitive_values(redactor):
    secrets = {"DB_PASSWORD": "s3cr3t", "DB_HOST": "localhost"}
    result = redactor.redact(secrets)
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER
    assert result["DB_HOST"] == "localhost"


def test_redact_does_not_mutate_original(redactor):
    secrets = {"API_KEY": "abc123"}
    redactor.redact(secrets)
    assert secrets["API_KEY"] == "abc123"


def test_redact_value_sensitive(redactor):
    assert redactor.redact_value("SECRET", "topsecret") == REDACTED_PLACEHOLDER


def test_redact_value_non_sensitive(redactor):
    assert redactor.redact_value("APP_ENV", "production") == "production"


def test_custom_placeholder():
    r = Redactor(placeholder="[HIDDEN]")
    assert r.redact_value("PASSWORD", "x") == "[HIDDEN]"


def test_build_redactor_includes_defaults():
    r = build_redactor()
    assert r.is_sensitive("secret_key") is True


def test_build_redactor_with_extra_patterns():
    r = build_redactor(extra_patterns=[r"(?i)ssn"])
    assert r.is_sensitive("USER_SSN") is True
    assert r.is_sensitive("DB_HOST") is False


def test_build_redactor_extra_does_not_remove_defaults():
    r = build_redactor(extra_patterns=[r"(?i)ssn"])
    assert r.is_sensitive("AUTH_TOKEN") is True


def test_redact_empty_dict(redactor):
    assert redactor.redact({}) == {}
