"""Tests for vault_sync.syncer module."""

from unittest.mock import MagicMock, patch
import pytest

from vault_sync.namespace import Namespace
from vault_sync.syncer import sync_secrets, SyncResult


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.read_secret.return_value = {"api_key": "abc123", "debug": "false"}
    return client


@pytest.fixture
def simple_namespace():
    return [Namespace(path="secret/app", prefix="APP")]


def test_sync_adds_new_keys(mock_client, simple_namespace, tmp_path):
    env_file = str(tmp_path / ".env")
    result = sync_secrets(mock_client, simple_namespace, env_file)
    assert "APP_API_KEY" in result.added
    assert "APP_DEBUG" in result.added
    assert result.updated == []


def test_sync_detects_updated_keys(mock_client, simple_namespace, tmp_path):
    env_file = str(tmp_path / ".env")
    # Pre-populate with old value
    env_file_path = tmp_path / ".env"
    env_file_path.write_text("APP_API_KEY=old_value\n")
    result = sync_secrets(mock_client, simple_namespace, str(env_file_path))
    assert "APP_API_KEY" in result.updated


def test_sync_detects_unchanged_keys(mock_client, simple_namespace, tmp_path):
    env_file_path = tmp_path / ".env"
    env_file_path.write_text('APP_API_KEY=abc123\n')
    result = sync_secrets(mock_client, simple_namespace, str(env_file_path))
    assert "APP_API_KEY" in result.unchanged


def test_sync_dry_run_does_not_write(mock_client, simple_namespace, tmp_path):
    env_file_path = tmp_path / ".env"
    sync_secrets(mock_client, simple_namespace, str(env_file_path), dry_run=True)
    assert not env_file_path.exists()


def test_sync_records_error_on_failed_path(simple_namespace, tmp_path):
    client = MagicMock()
    client.read_secret.side_effect = Exception("connection refused")
    env_file = str(tmp_path / ".env")
    result = sync_secrets(client, simple_namespace, env_file)
    assert "secret/app" in result.errors


def test_sync_result_total():
    r = SyncResult()
    r.added = ["A", "B"]
    r.updated = ["C"]
    r.unchanged = ["D", "E", "F"]
    assert r.total == 6


def test_sync_writes_file(mock_client, simple_namespace, tmp_path):
    env_file_path = tmp_path / ".env"
    sync_secrets(mock_client, simple_namespace, str(env_file_path))
    assert env_file_path.exists()
    content = env_file_path.read_text()
    assert "APP_API_KEY" in content
