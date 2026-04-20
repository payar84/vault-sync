"""Tests for vault_sync.expiry_command."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vault_sync.expiry_command import build_expiry_parser, run_expiry_command


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def records_file(tmp_path: Path) -> Path:
    return tmp_path / "records.json"


def _ts(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


def _run(records_file: Path, extra: list | None = None):
    parser = build_expiry_parser()
    argv = ["--records", str(records_file)] + (extra or [])
    args = parser.parse_args(argv)
    return run_expiry_command(args)


def test_missing_records_file_returns_one(records_file: Path):
    rc = _run(records_file)  # file does not exist yet
    assert rc == 1


def test_invalid_json_returns_one(records_file: Path):
    records_file.write_text("not-json")
    rc = _run(records_file)
    assert rc == 1


def test_all_current_returns_zero(records_file: Path):
    data = {"secret/app": _ts(5)}
    records_file.write_text(json.dumps(data))
    rc = _run(records_file)
    assert rc == 0


def test_expired_without_fail_flag_returns_zero(records_file: Path):
    data = {"secret/old": _ts(200)}
    records_file.write_text(json.dumps(data))
    rc = _run(records_file)
    assert rc == 0


def test_expired_with_fail_flag_returns_one(records_file: Path):
    data = {"secret/old": _ts(200)}
    records_file.write_text(json.dumps(data))
    rc = _run(records_file, ["--fail-on-expired"])
    assert rc == 1


def test_invalid_config_returns_one(records_file: Path):
    data = {"secret/app": _ts(5)}
    records_file.write_text(json.dumps(data))
    rc = _run(records_file, ["--max-age-days", "0"])
    assert rc == 1


def test_warn_before_must_be_less_than_max_age(records_file: Path):
    data = {"secret/app": _ts(5)}
    records_file.write_text(json.dumps(data))
    rc = _run(records_file, ["--max-age-days", "30", "--warn-before-days", "30"])
    assert rc == 1
