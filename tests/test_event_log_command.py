"""Tests for vault_sync.event_log_command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vault_sync.event_log import EventLog, EventType
from vault_sync.event_log_command import build_event_log_parser, run_event_log_command


@pytest.fixture
def log_file(tmp_path) -> Path:
    return tmp_path / "events.json"


def _make_log(path: Path, *events) -> None:
    log = EventLog()
    for et, msg in events:
        log.record(et, msg)
    log.write(path)


def _run(args, log_file):
    parser = build_event_log_parser()
    parsed = parser.parse_args(["--log-file", str(log_file)] + args)
    return run_event_log_command(parsed)


def test_show_empty_log_returns_zero(log_file):
    _make_log(log_file)
    assert _run(["show"], log_file) == 0


def test_show_lists_events(log_file, capsys):
    _make_log(log_file, (EventType.SYNC_STARTED, "started"))
    _run(["show"], log_file)
    out = capsys.readouterr().out
    assert "sync_started" in out
    assert "started" in out


def test_show_json_flag(log_file, capsys):
    _make_log(log_file, (EventType.AUTH_SUCCESS, "ok"))
    _run(["show", "--json"], log_file)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["event_type"] == "auth_success"


def test_show_filter_by_type(log_file, capsys):
    _make_log(
        log_file,
        (EventType.SYNC_STARTED, "a"),
        (EventType.SECRET_READ, "b"),
    )
    _run(["show", "--type", "sync_started"], log_file)
    out = capsys.readouterr().out
    assert "sync_started" in out
    assert "secret_read" not in out


def test_show_invalid_type_returns_one(log_file):
    _make_log(log_file)
    assert _run(["show", "--type", "not_a_type"], log_file) == 1


def test_clear_empties_log(log_file):
    _make_log(log_file, (EventType.SYNC_COMPLETED, "done"))
    _run(["clear"], log_file)
    log = EventLog()
    log.load(log_file)
    assert log.all_events() == []


def test_types_lists_all_event_types(log_file, capsys):
    _make_log(log_file)
    _run(["types"], log_file)
    out = capsys.readouterr().out
    for et in EventType:
        assert et.value in out
