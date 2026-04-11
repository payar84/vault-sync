"""Tests for vault_sync.schema — SecretSchema and FieldSchema validation."""
import pytest

from vault_sync.schema import FieldSchema, FieldType, SecretSchema


# ---------------------------------------------------------------------------
# FieldSchema.validate_value
# ---------------------------------------------------------------------------

def test_string_field_accepts_any_value():
    f = FieldSchema(name="KEY", type=FieldType.STRING)
    assert f.validate_value("hello world") is None


def test_integer_field_rejects_non_integer():
    f = FieldSchema(name="PORT", type=FieldType.INTEGER)
    err = f.validate_value("abc")
    assert err is not None
    assert "PORT" in err


def test_integer_field_accepts_valid_integer():
    f = FieldSchema(name="PORT", type=FieldType.INTEGER)
    assert f.validate_value("8080") is None


def test_integer_field_accepts_negative():
    f = FieldSchema(name="OFFSET", type=FieldType.INTEGER)
    assert f.validate_value("-1") is None


def test_boolean_field_accepts_true_false():
    f = FieldSchema(name="FLAG", type=FieldType.BOOLEAN)
    for val in ("true", "false", "True", "False", "1", "0"):
        assert f.validate_value(val) is None


def test_boolean_field_rejects_invalid():
    f = FieldSchema(name="FLAG", type=FieldType.BOOLEAN)
    assert f.validate_value("yes") is not None


def test_url_field_accepts_https():
    f = FieldSchema(name="ENDPOINT", type=FieldType.URL)
    assert f.validate_value("https://example.com") is None


def test_url_field_rejects_plain_string():
    f = FieldSchema(name="ENDPOINT", type=FieldType.URL)
    assert f.validate_value("example.com") is not None


def test_email_field_accepts_valid():
    f = FieldSchema(name="CONTACT", type=FieldType.EMAIL)
    assert f.validate_value("user@example.com") is None


def test_email_field_rejects_invalid():
    f = FieldSchema(name="CONTACT", type=FieldType.EMAIL)
    assert f.validate_value("not-an-email") is not None


def test_pattern_constraint_passes():
    f = FieldSchema(name="CODE", pattern=r"[A-Z]{3}-\d{4}")
    assert f.validate_value("ABC-1234") is None


def test_pattern_constraint_fails():
    f = FieldSchema(name="CODE", pattern=r"[A-Z]{3}-\d{4}")
    err = f.validate_value("abc-1234")
    assert err is not None
    assert "CODE" in err


# ---------------------------------------------------------------------------
# SecretSchema.validate
# ---------------------------------------------------------------------------

def _schema(*fields):
    return SecretSchema(fields=list(fields))


def test_missing_required_key_is_error():
    schema = _schema(FieldSchema(name="DB_URL", type=FieldType.URL))
    errors = schema.validate({})
    assert any("DB_URL" in e for e in errors)


def test_missing_optional_key_is_not_error():
    schema = _schema(FieldSchema(name="DEBUG", type=FieldType.BOOLEAN, required=False))
    errors = schema.validate({})
    assert errors == []


def test_all_valid_returns_empty_list():
    schema = _schema(
        FieldSchema(name="PORT", type=FieldType.INTEGER),
        FieldSchema(name="HOST", type=FieldType.STRING),
    )
    errors = schema.validate({"PORT": "5432", "HOST": "localhost"})
    assert errors == []


def test_multiple_errors_are_collected():
    schema = _schema(
        FieldSchema(name="PORT", type=FieldType.INTEGER),
        FieldSchema(name="URL", type=FieldType.URL),
    )
    errors = schema.validate({"PORT": "bad", "URL": "bad"})
    assert len(errors) == 2
