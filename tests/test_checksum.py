"""Tests for vault_sync.checksum."""
import json
from pathlib import Path

import pytest

from vault_sync.checksum import (
    ChecksumRecord,
    _sha256_of_dict,
    _sha256_of_file,
    compute_record,
    verify_record,
)


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return p


def test_sha256_of_dict_is_stable():
    d = {"B": "2", "A": "1"}
    assert _sha256_of_dict(d) == _sha256_of_dict(d)


def test_sha256_of_dict_is_order_independent():
    d1 = {"A": "1", "B": "2"}
    d2 = {"B": "2", "A": "1"}
    assert _sha256_of_dict(d1) == _sha256_of_dict(d2)


def test_sha256_of_dict_differs_on_value_change():
    d1 = {"A": "1"}
    d2 = {"A": "2"}
    assert _sha256_of_dict(d1) != _sha256_of_dict(d2)


def test_sha256_of_file_returns_none_when_missing(tmp_path: Path):
    assert _sha256_of_file(tmp_path / "nonexistent.env") is None


def test_sha256_of_file_returns_string_for_existing_file(tmp_env: Path):
    result = _sha256_of_file(tmp_env)
    assert isinstance(result, str) and len(result) == 64


def test_compute_record_has_secrets_digest():
    record = compute_record({"KEY": "val"})
    assert len(record.secrets_digest) == 64


def test_compute_record_file_digest_none_without_path():
    record = compute_record({"KEY": "val"})
    assert record.file_digest is None


def test_compute_record_file_digest_set_with_path(tmp_env: Path):
    record = compute_record({"KEY": "val"}, env_path=tmp_env)
    assert record.file_digest is not None


def test_verify_record_secrets_match():
    secrets = {"A": "1", "B": "2"}
    record = compute_record(secrets)
    result = verify_record(record, secrets)
    assert result["secrets_match"] is True


def test_verify_record_secrets_mismatch():
    secrets = {"A": "1"}
    record = compute_record(secrets)
    result = verify_record(record, {"A": "changed"})
    assert result["secrets_match"] is False


def test_verify_record_file_match(tmp_env: Path):
    secrets = {"K": "v"}
    record = compute_record(secrets, env_path=tmp_env)
    result = verify_record(record, secrets, env_path=tmp_env)
    assert result["file_match"] is True


def test_verify_record_file_mismatch(tmp_env: Path):
    secrets = {"K": "v"}
    record = compute_record(secrets, env_path=tmp_env)
    tmp_env.write_text("KEY=modified\n")
    result = verify_record(record, secrets, env_path=tmp_env)
    assert result["file_match"] is False


def test_checksum_record_roundtrip():
    original = ChecksumRecord(secrets_digest="abc123", file_digest="def456")
    restored = ChecksumRecord.from_dict(original.to_dict())
    assert restored.secrets_digest == original.secrets_digest
    assert restored.file_digest == original.file_digest
