"""Tests for vault_sync.schema_loader."""
import json
import pytest

from vault_sync.schema import FieldType
from vault_sync.schema_loader import load_schema_file, load_schema_or_default


@pytest.fixture()
def json_schema_file(tmp_path):
    data = {
        "fields": [
            {"name": "API_URL", "type": "url", "required": True},
            {"name": "PORT", "type": "integer", "required": False},
            {"name": "TAG", "type": "string", "pattern": "[a-z]+"},
        ]
    }
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_load_json_returns_schema(json_schema_file):
    schema = load_schema_file(json_schema_file)
    assert len(schema.fields) == 3


def test_load_json_field_names(json_schema_file):
    schema = load_schema_file(json_schema_file)
    names = [f.name for f in schema.fields]
    assert "API_URL" in names
    assert "PORT" in names


def test_load_json_field_types(json_schema_file):
    schema = load_schema_file(json_schema_file)
    by_name = {f.name: f for f in schema.fields}
    assert by_name["API_URL"].type == FieldType.URL
    assert by_name["PORT"].type == FieldType.INTEGER


def test_load_json_optional_field(json_schema_file):
    schema = load_schema_file(json_schema_file)
    by_name = {f.name: f for f in schema.fields}
    assert by_name["PORT"].required is False


def test_load_json_pattern_field(json_schema_file):
    schema = load_schema_file(json_schema_file)
    by_name = {f.name: f for f in schema.fields}
    assert by_name["TAG"].pattern == "[a-z]+"


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_schema_file("/nonexistent/schema.json")


def test_load_unsupported_format_raises(tmp_path):
    p = tmp_path / "schema.toml"
    p.write_text("")
    with pytest.raises(ValueError, match="Unsupported"):
        load_schema_file(str(p))


def test_load_schema_or_default_none_returns_empty():
    schema = load_schema_or_default(None)
    assert schema.fields == []


def test_load_schema_or_default_path_returns_schema(json_schema_file):
    schema = load_schema_or_default(json_schema_file)
    assert len(schema.fields) == 3


def test_empty_schema_validates_anything():
    from vault_sync.schema import SecretSchema
    schema = SecretSchema()
    assert schema.validate({"ANY_KEY": "any_value"}) == []
