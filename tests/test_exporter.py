"""Tests for vault_sync.exporter."""
import json
import pytest
from pathlib import Path

from vault_sync.exporter import (
    ExportFormat,
    export_secrets,
    parse_export_format,
)


@pytest.fixture
def secrets():
    return {
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "APP_HOST": "localhost",
        "GREETING": "hello world",
    }


def test_dotenv_output_is_sorted(secrets):
    result = export_secrets(secrets, ExportFormat.DOTENV)
    keys = [line.split("=")[0] for line in result.strip().splitlines()]
    assert keys == sorted(keys)


def test_dotenv_quotes_values_with_spaces(secrets):
    result = export_secrets(secrets, ExportFormat.DOTENV)
    assert 'GREETING="hello world"' in result


def test_dotenv_plain_values_are_unquoted(secrets):
    result = export_secrets(secrets, ExportFormat.DOTENV)
    assert "API_KEY=abc123" in result


def test_json_output_is_valid(secrets):
    result = export_secrets(secrets, ExportFormat.JSON)
    parsed = json.loads(result)
    assert parsed["API_KEY"] == "abc123"
    assert parsed["DB_PASSWORD"] == "s3cr3t"


def test_json_keys_are_sorted(secrets):
    result = export_secrets(secrets, ExportFormat.JSON)
    parsed = json.loads(result)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_yaml_output_contains_all_keys(secrets):
    result = export_secrets(secrets, ExportFormat.YAML)
    for key in secrets:
        assert key in result


def test_yaml_quotes_values_with_colon():
    result = export_secrets({"URL": "http://example.com"}, ExportFormat.YAML)
    assert '"http://example.com"' in result


def test_export_writes_file(tmp_path, secrets):
    out = tmp_path / "output.env"
    export_secrets(secrets, ExportFormat.DOTENV, output_path=out)
    assert out.exists()
    assert "API_KEY=abc123" in out.read_text()


def test_export_returns_content_even_when_writing(tmp_path, secrets):
    out = tmp_path / "output.json"
    content = export_secrets(secrets, ExportFormat.JSON, output_path=out)
    assert isinstance(content, str)
    assert json.loads(content)["APP_HOST"] == "localhost"


def test_parse_export_format_valid():
    assert parse_export_format("json") == ExportFormat.JSON
    assert parse_export_format("YAML") == ExportFormat.YAML
    assert parse_export_format("dotenv") == ExportFormat.DOTENV


def test_parse_export_format_invalid():
    with pytest.raises(ValueError, match="Unknown export format"):
        parse_export_format("toml")


def test_empty_secrets_returns_empty_string():
    assert export_secrets({}, ExportFormat.DOTENV) == ""
    assert export_secrets({}, ExportFormat.YAML) == ""
