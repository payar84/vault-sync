"""Tests for vault_sync.merge_command."""
import pytest
from pathlib import Path
from vault_sync.merge_command import build_merge_parser, run_merge_command
from vault_sync.env_writer import read_env_file


@pytest.fixture()
def source_env(tmp_path: Path) -> Path:
    p = tmp_path / "vault.env"
    p.write_text("DB_HOST=vault-host\nNEW_KEY=hello\n")
    return p


@pytest.fixture()
def target_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=local-host\nLOCAL_ONLY=keep\n")
    return p


def _run(args_list, tmp_path=None):
    parser = build_merge_parser()
    args = parser.parse_args(args_list)
    return run_merge_command(args)


def test_vault_wins_overwrites_target(source_env, target_env):
    code = _run([str(target_env), "--source", str(source_env), "--strategy", "vault_wins"])
    assert code == 0
    result = read_env_file(target_env)
    assert result["DB_HOST"] == "vault-host"


def test_local_wins_preserves_target(source_env, target_env):
    code = _run([str(target_env), "--source", str(source_env), "--strategy", "local_wins"])
    assert code == 0
    result = read_env_file(target_env)
    assert result["DB_HOST"] == "local-host"


def test_new_keys_are_added_regardless_of_strategy(source_env, target_env):
    code = _run([str(target_env), "--source", str(source_env), "--strategy", "local_wins"])
    assert code == 0
    result = read_env_file(target_env)
    assert result["NEW_KEY"] == "hello"


def test_missing_source_returns_one(target_env, tmp_path):
    missing = tmp_path / "nope.env"
    code = _run([str(target_env), "--source", str(missing)])
    assert code == 1


def test_invalid_strategy_returns_one(source_env, target_env):
    code = _run([str(target_env), "--source", str(source_env), "--strategy", "bogus"])
    assert code == 1


def test_dry_run_does_not_write(source_env, target_env):
    original = target_env.read_text()
    code = _run([str(target_env), "--source", str(source_env), "--dry-run"])
    assert code == 0
    assert target_env.read_text() == original


def test_target_created_when_missing(source_env, tmp_path):
    new_target = tmp_path / "new.env"
    code = _run([str(new_target), "--source", str(source_env)])
    assert code == 0
    assert new_target.exists()
    result = read_env_file(new_target)
    assert "DB_HOST" in result
