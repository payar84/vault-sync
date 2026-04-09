"""Tests for vault_sync.backup module."""

import pytest
from pathlib import Path

from vault_sync.backup import BackupMeta, create_backup, restore_backup, list_backups


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret\nDEBUG=true\n")
    return p


def test_create_backup_returns_meta(env_file, tmp_path):
    backup_dir = tmp_path / "backups"
    meta = create_backup(env_file, backup_dir=backup_dir)
    assert meta is not None
    assert isinstance(meta, BackupMeta)


def test_backup_file_exists(env_file, tmp_path):
    backup_dir = tmp_path / "backups"
    meta = create_backup(env_file, backup_dir=backup_dir)
    assert Path(meta.backup).exists()


def test_backup_content_matches_original(env_file, tmp_path):
    backup_dir = tmp_path / "backups"
    meta = create_backup(env_file, backup_dir=backup_dir)
    assert Path(meta.backup).read_text() == env_file.read_text()


def test_create_backup_returns_none_if_missing(tmp_path):
    missing = tmp_path / ".env"
    result = create_backup(missing)
    assert result is None


def test_backup_dir_is_created_automatically(env_file, tmp_path):
    backup_dir = tmp_path / "nested" / "backups"
    assert not backup_dir.exists()
    create_backup(env_file, backup_dir=backup_dir)
    assert backup_dir.exists()


def test_to_dict_contains_expected_keys(env_file, tmp_path):
    meta = create_backup(env_file, backup_dir=tmp_path / "backups")
    d = meta.to_dict()
    assert "original" in d
    assert "backup" in d
    assert "created_at" in d


def test_restore_backup_overwrites_original(env_file, tmp_path):
    backup_dir = tmp_path / "backups"
    meta = create_backup(env_file, backup_dir=backup_dir)
    env_file.write_text("CHANGED=yes\n")
    restore_backup(meta)
    assert "API_KEY=secret" in env_file.read_text()


def test_restore_raises_if_backup_missing(tmp_path):
    meta = BackupMeta(
        original=tmp_path / ".env",
        backup=tmp_path / "nonexistent.bak",
    )
    with pytest.raises(FileNotFoundError):
        restore_backup(meta)


def test_list_backups_returns_sorted_paths(env_file, tmp_path):
    backup_dir = tmp_path / "backups"
    create_backup(env_file, backup_dir=backup_dir)
    create_backup(env_file, backup_dir=backup_dir)
    backups = list_backups(env_file, backup_dir=backup_dir)
    assert len(backups) == 2
    assert backups == sorted(backups)


def test_list_backups_empty_if_no_backup_dir(env_file, tmp_path):
    result = list_backups(env_file, backup_dir=tmp_path / "nonexistent")
    assert result == []
