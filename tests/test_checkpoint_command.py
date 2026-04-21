"""Tests for vault_sync.checkpoint_command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vault_sync.checkpoint_command import build_checkpoint_parser, run_checkpoint_command


@pytest.fixture
def cp_file(tmp_path: Path) -> Path:
    return tmp_path / "cp.json"


def _run(args: list, cp_file: Path) -> int:
    parser = build_checkpoint_parser()
    ns = parser.parse_args(["--file", str(cp_file)] + args)
    return run_checkpoint_command(ns)


def test_list_empty_returns_zero(cp_file: Path):
    assert _run(["list"], cp_file) == 0


def test_mark_returns_zero(cp_file: Path):
    assert _run(["mark", "secret/app", "--key-count", "3", "--checksum", "abc"], cp_file) == 0


def test_mark_writes_file(cp_file: Path):
    _run(["mark", "secret/app", "--key-count", "5", "--checksum", "xyz"], cp_file)
    assert cp_file.exists()
    data = json.loads(cp_file.read_text())
    assert "secret/app" in data
    assert data["secret/app"]["key_count"] == 5


def test_list_after_mark_returns_zero(cp_file: Path):
    _run(["mark", "secret/db", "--key-count", "2", "--checksum", "h1"], cp_file)
    assert _run(["list"], cp_file) == 0


def test_clear_specific_path_returns_zero(cp_file: Path):
    _run(["mark", "secret/db", "--key-count", "2", "--checksum", "h1"], cp_file)
    assert _run(["clear", "--path", "secret/db"], cp_file) == 0


def test_clear_all_returns_zero(cp_file: Path):
    _run(["mark", "secret/db", "--key-count", "2", "--checksum", "h1"], cp_file)
    assert _run(["clear"], cp_file) == 0


def test_clear_all_empties_file(cp_file: Path):
    _run(["mark", "secret/db", "--key-count", "2", "--checksum", "h1"], cp_file)
    _run(["clear"], cp_file)
    data = json.loads(cp_file.read_text())
    assert data == {}


def test_invalid_max_entries_returns_one(cp_file: Path):
    assert _run(["--max-entries", "0", "list"], cp_file) == 1


def test_invalid_ttl_returns_one(cp_file: Path):
    assert _run(["--ttl", "0", "list"], cp_file) == 1
