"""Tests for vault_sync.event_log."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vault_sync.event_log import Event, EventLog, EventType


@pytest.fixture
def log() -> EventLog:
    return EventLog()


def test_record_adds_event(log):
    log.record(EventType.SYNC_STARTED, "sync began")
    assert len(log.all_events()) == 1


def test_event_fields_are_set(log):
    evt = log.record(EventType.AUTH_SUCCESS, "authenticated", user="root")
    assert evt.event_type == EventType.AUTH_SUCCESS
    assert evt.message == "authenticated"
    assert evt.metadata["user"] == "root"


def test_event_timestamp_is_iso(log):
    evt = log.record(EventType.SYNC_COMPLETED, "done")
    assert "T" in evt.timestamp


def test_filter_by_type_returns_matching(log):
    log.record(EventType.SYNC_STARTED, "a")
    log.record(EventType.SECRET_READ, "b")
    log.record(EventType.SYNC_STARTED, "c")
    results = log.filter_by_type(EventType.SYNC_STARTED)
    assert len(results) == 2


def test_filter_by_type_empty_when_none_match(log):
    log.record(EventType.SYNC_STARTED, "a")
    results = log.filter_by_type(EventType.AUTH_FAILURE)
    assert results == []


def test_to_dict_contains_required_keys(log):
    evt = log.record(EventType.SECRET_WRITE, "written")
    d = evt.to_dict()
    assert set(d.keys()) == {"event_type", "message", "timestamp", "metadata"}


def test_write_creates_json_file(log, tmp_path):
    log.record(EventType.SYNC_COMPLETED, "ok")
    out = tmp_path / "events.json"
    log.write(out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert data[0]["event_type"] == "sync_completed"


def test_load_reads_existing_file(tmp_path):
    data = [
        {
            "event_type": "auth_success",
            "message": "ok",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "metadata": {},
        }
    ]
    f = tmp_path / "events.json"
    f.write_text(json.dumps(data))
    log = EventLog()
    log.load(f)
    assert len(log.all_events()) == 1
    assert log.all_events()[0].event_type == EventType.AUTH_SUCCESS


def test_load_missing_file_is_noop(tmp_path):
    log = EventLog()
    log.load(tmp_path / "nonexistent.json")
    assert log.all_events() == []


def test_clear_removes_all_events(log):
    log.record(EventType.SYNC_STARTED, "a")
    log.record(EventType.SYNC_COMPLETED, "b")
    log.clear()
    assert log.all_events() == []
