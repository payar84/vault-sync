"""Tests for vault_sync.rotation_command."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from vault_sync.rotation_command import build_rotation_parser, run_rotation_command


@pytest.fixture
def records_file(tmp_path: Path) -> Path:
    return tmp_path / ".rotation_records.json"


def _run(args_list, records_file):
    parser = build_rotation_parser()
    args = parser.parse_args(args_list + ["--records-file", str(records_file)])
    if not hasattr(args, "rotation_action") or args.rotation_action is None:
        args.rotation_action = "check"
    return run_rotation_command(args)


def test_check_empty_records_exits_zero(records_file):
    rc = _run([], records_file)
    assert rc == 0


def test_mark_writes_records(records_file):
    _run(["mark", "DB_PASSWORD", "API_KEY"], records_file)
    data = json.loads(records_file.read_text())
    assert "DB_PASSWORD" in data
    assert "API_KEY" in data


def test_mark_timestamps_are_iso(records_file):
    _run(["mark", "TOKEN"], records_file)
    data = json.loads(records_file.read_text())
    datetime.fromisoformat(data["TOKEN"])  # should not raise


def test_check_fresh_key_exits_zero(records_file):
    _run(["mark", "FRESH_KEY"], records_file)
    rc = _run(["check", "FRESH_KEY"], records_file)
    assert rc == 0


def test_fail_on_expired_returns_nonzero(records_file):
    parser = build_rotation_parser()
    args = parser.parse_args(
        ["--fail-on-expired", "--records-file", str(records_file), "MISSING_KEY"]
    )
    args.rotation_action = "check"
    rc = run_rotation_command(args)
    assert rc == 1


def test_no_fail_on_expired_returns_zero(records_file):
    parser = build_rotation_parser()
    args = parser.parse_args(["--records-file", str(records_file), "MISSING_KEY"])
    args.rotation_action = "check"
    rc = run_rotation_command(args)
    assert rc == 0


def test_check_uses_all_records_when_no_keys_given(records_file):
    _run(["mark", "A", "B"], records_file)
    rc = _run([], records_file)
    assert rc == 0
