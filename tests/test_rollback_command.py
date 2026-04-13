from __future__ import annotations

import pytest
from pathlib import Path

from vault_sync.backup import create_backup
from vault_sync.rollback_command import build_rollback_parser, run_rollback_command


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=hello\n")
    return p


@pytest.fixture()
def backup_dir(tmp_path: Path) -> Path:
    d = tmp_path / "backups"
    d.mkdir()
    return d


def _run(args_list, env_file, backup_dir):
    parser = build_rollback_parser()
    args = parser.parse_args(
        ["--env-file", str(env_file), "--backup-dir", str(backup_dir)] + args_list
    )
    return run_rollback_command(args)


def test_latest_returns_zero_on_success(env_file, backup_dir):
    create_backup(env_file, backup_dir)
    env_file.write_text("KEY=changed\n")
    rc = _run(["latest"], env_file, backup_dir)
    assert rc == 0


def test_latest_returns_one_when_no_backup(env_file, backup_dir):
    rc = _run(["latest"], env_file, backup_dir)
    assert rc == 1


def test_to_returns_zero_on_match(env_file, backup_dir):
    meta = create_backup(env_file, backup_dir)
    env_file.write_text("KEY=changed\n")
    prefix = meta.timestamp[:10]
    rc = _run(["to", prefix], env_file, backup_dir)
    assert rc == 0


def test_to_returns_one_on_no_match(env_file, backup_dir):
    create_backup(env_file, backup_dir)
    rc = _run(["to", "1999-01-01"], env_file, backup_dir)
    assert rc == 1


def test_list_returns_zero(env_file, backup_dir, capsys):
    create_backup(env_file, backup_dir)
    rc = _run(["list"], env_file, backup_dir)
    assert rc == 0
    out = capsys.readouterr().out
    assert ".env" in out


def test_list_prints_no_backups_when_empty(env_file, backup_dir, capsys):
    rc = _run(["list"], env_file, backup_dir)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No backups" in out
