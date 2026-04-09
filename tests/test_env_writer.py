"""Tests for vault_sync.env_writer."""

import os
import textwrap
from pathlib import Path

import pytest

from vault_sync.env_writer import read_env_file, write_env_file


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def test_write_creates_file(tmp_env: Path) -> None:
    written = write_env_file({"DB_HOST": "localhost", "DB_PORT": "5432"}, str(tmp_env))
    assert written == 2
    assert tmp_env.exists()


def test_written_content_is_sorted(tmp_env: Path) -> None:
    write_env_file({"Z_KEY": "z", "A_KEY": "a"}, str(tmp_env))
    lines = tmp_env.read_text().splitlines()
    assert lines[0].startswith("A_KEY")
    assert lines[1].startswith("Z_KEY")


def test_values_with_spaces_are_quoted(tmp_env: Path) -> None:
    write_env_file({"MSG": "hello world"}, str(tmp_env))
    content = tmp_env.read_text()
    assert 'MSG="hello world"' in content


def test_read_env_file_parses_correctly(tmp_env: Path) -> None:
    tmp_env.write_text(textwrap.dedent("""\
        # comment
        KEY1=value1
        KEY2="spaced value"
    """))
    result = read_env_file(str(tmp_env))
    assert result == {"KEY1": "value1", "KEY2": "spaced value"}


def test_read_missing_file_returns_empty(tmp_path: Path) -> None:
    result = read_env_file(str(tmp_path / "nonexistent.env"))
    assert result == {}


def test_overwrite_false_preserves_existing_keys(tmp_env: Path) -> None:
    write_env_file({"EXISTING": "old"}, str(tmp_env))
    write_env_file({"EXISTING": "new", "FRESH": "yes"}, str(tmp_env), overwrite=False)
    result = read_env_file(str(tmp_env))
    # existing key should NOT be overwritten
    assert result["EXISTING"] == "old"
    assert result["FRESH"] == "yes"


def test_overwrite_true_replaces_all_keys(tmp_env: Path) -> None:
    write_env_file({"KEY": "original"}, str(tmp_env))
    write_env_file({"KEY": "updated"}, str(tmp_env), overwrite=True)
    result = read_env_file(str(tmp_env))
    assert result["KEY"] == "updated"
