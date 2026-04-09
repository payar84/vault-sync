"""Tests for vault_sync.audit module."""

import json
from pathlib import Path

import pytest

from vault_sync.audit import AuditEntry, AuditLog


@pytest.fixture
def audit_log() -> AuditLog:
    return AuditLog()


def test_record_adds_entry(audit_log: AuditLog) -> None:
    audit_log.record(action="sync", path="secret/app", key="DB_URL", status="added")
    assert len(audit_log.entries) == 1


def test_entry_fields_are_set(audit_log: AuditLog) -> None:
    audit_log.record(action="sync", path="secret/app", key="API_KEY", status="updated", namespace="prod")
    entry = audit_log.entries[0]
    assert entry.action == "sync"
    assert entry.path == "secret/app"
    assert entry.key == "API_KEY"
    assert entry.status == "updated"
    assert entry.namespace == "prod"


def test_entry_timestamp_is_iso_format(audit_log: AuditLog) -> None:
    audit_log.record(action="sync", path="secret/app", key="TOKEN", status="unchanged")
    entry = audit_log.entries[0]
    # Should not raise
    from datetime import datetime
    datetime.fromisoformat(entry.timestamp)


def test_to_dict_contains_all_keys(audit_log: AuditLog) -> None:
    audit_log.record(action="sync", path="secret/app", key="FOO", status="added")
    d = audit_log.entries[0].to_dict()
    assert set(d.keys()) == {"timestamp", "action", "path", "key", "status", "namespace"}


def test_summary_counts_statuses(audit_log: AuditLog) -> None:
    audit_log.record(action="sync", path="p", key="A", status="added")
    audit_log.record(action="sync", path="p", key="B", status="added")
    audit_log.record(action="sync", path="p", key="C", status="unchanged")
    summary = audit_log.summary()
    assert summary["added"] == 2
    assert summary["unchanged"] == 1


def test_write_creates_valid_json(audit_log: AuditLog, tmp_path: Path) -> None:
    audit_log.record(action="sync", path="secret/db", key="PASSWORD", status="added")
    audit_log.record(action="sync", path="secret/db", key="HOST", status="unchanged")
    out = tmp_path / "audit.json"
    audit_log.write(out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["key"] == "PASSWORD"


def test_write_empty_log(audit_log: AuditLog, tmp_path: Path) -> None:
    out = tmp_path / "audit.json"
    audit_log.write(out)
    data = json.loads(out.read_text())
    assert data == []
