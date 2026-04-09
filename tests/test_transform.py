"""Tests for vault_sync.transform."""
import pytest

from vault_sync.transform import (
    apply_transforms,
    mask_sensitive,
    strip_whitespace,
    to_uppercase_value,
    DEFAULT_TRANSFORMERS,
)


def test_strip_whitespace_removes_spaces():
    assert strip_whitespace("KEY", "  hello  ") == "hello"


def test_strip_whitespace_leaves_inner_spaces():
    assert strip_whitespace("KEY", "hello world") == "hello world"


def test_to_uppercase_value():
    assert to_uppercase_value("KEY", "hello") == "HELLO"


def test_mask_sensitive_password():
    assert mask_sensitive("DB_PASSWORD", "s3cr3t") == "***"


def test_mask_sensitive_token():
    assert mask_sensitive("API_TOKEN", "abc123") == "***"


def test_mask_sensitive_key():
    assert mask_sensitive("PRIVATE_KEY", "rsa...") == "***"


def test_mask_sensitive_non_sensitive_key():
    assert mask_sensitive("DB_HOST", "localhost") == "localhost"


def test_apply_transforms_single():
    secrets = {"KEY": "  value  "}
    result = apply_transforms(secrets, [strip_whitespace])
    assert result == {"KEY": "value"}


def test_apply_transforms_chain():
    secrets = {"KEY": "  hello  "}
    result = apply_transforms(secrets, [strip_whitespace, to_uppercase_value])
    assert result == {"KEY": "HELLO"}


def test_apply_transforms_empty_secrets():
    assert apply_transforms({}, [strip_whitespace]) == {}


def test_apply_transforms_no_transformers():
    secrets = {"KEY": "value"}
    assert apply_transforms(secrets, []) == {"KEY": "value"}


def test_default_transformers_strip_whitespace():
    secrets = {"KEY": "  trimmed  "}
    result = apply_transforms(secrets, DEFAULT_TRANSFORMERS)
    assert result == {"KEY": "trimmed"}
