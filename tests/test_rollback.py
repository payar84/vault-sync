from __future__ import annotations

import pytest
from pathlib import Path

from vault_sync.backup import create_backup
from vault_sync.rollback import (
    RollbackResult,
    rollback_to_latest,
    rollback_to_timestamp,
    safe_sync_with_rollback,
)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=original\n")
    return p


@pytest.fixture()
def backup_dir(tmp_path: Path) -> Path:
    d = tmp_path / "backups"
    d.mkdir()
    return d


# --- RollbackResult helpers ---

def test_rollback_result_ok_is_success():
    from vault_sync.backup import BackupMeta
    meta = BackupMeta(original_path=".env", backup_path=".env.bak", timestamp="2024-01-01T00:00:00")
    r = RollbackResult.ok(meta)
    assert r.success is True
    assert r.backup_used is meta


def test_rollback_result_fail_is_not_success():
    r = RollbackResult.fail("oops")
    assert r.success is False
    assert "oops" in r.message


def test_rollback_result_repr_ok():
    from vault_sync.backup import BackupMeta
    meta = BackupMeta(original_path=".env", backup_path=".env.bak", timestamp="2024-01-01T00:00:00")
    r = RollbackResult.ok(meta)
    assert "ok" in repr(r)


def test_rollback_result_repr_fail():
    r = RollbackResult.fail("gone")
    assert "fail" in repr(r)


# --- rollback_to_latest ---

def test_rollback_to_latest_restores_content(env_file, backup_dir):
    create_backup(env_file, backup_dir)
    env_file.write_text("KEY=changed\n")
    result = rollback_to_latest(env_file, backup_dir)
    assert result.success
    assert env_file.read_text() == "KEY=original\n"


def test_rollback_to_latest_fails_when_no_backups(env_file, backup_dir):
    result = rollback_to_latest(env_file, backup_dir)
    assert not result.success
    assert "No backups" in result.message


# --- rollback_to_timestamp ---

def test_rollback_to_timestamp_matches_prefix(env_file, backup_dir):
    meta = create_backup(env_file, backup_dir)
    env_file.write_text("KEY=new\n")
    prefix = meta.timestamp[:10]  # date portion
    result = rollback_to_timestamp(env_file, backup_dir, prefix)
    assert result.success
    assert env_file.read_text() == "KEY=original\n"


def test_rollback_to_timestamp_fails_on_no_match(env_file, backup_dir):
    create_backup(env_file, backup_dir)
    result = rollback_to_timestamp(env_file, backup_dir, "1999-01-01")
    assert not result.success
    assert "No backup matching" in result.message


# --- safe_sync_with_rollback ---

def test_safe_sync_succeeds_and_keeps_new_content(env_file, backup_dir):
    def sync():
        env_file.write_text("KEY=synced\n")

    result = safe_sync_with_rollback(env_file, backup_dir, sync)
    assert result.success
    assert env_file.read_text() == "KEY=synced\n"


def test_safe_sync_rolls_back_on_exception(env_file, backup_dir):
    def sync():
        env_file.write_text("KEY=bad\n")
        raise RuntimeError("boom")

    result = safe_sync_with_rollback(env_file, backup_dir, sync)
    assert not result.success
    assert env_file.read_text() == "KEY=original\n"
    assert "rolled back" in result.message
