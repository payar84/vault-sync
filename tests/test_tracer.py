"""Tests for vault_sync.tracer."""
import pytest
from vault_sync.tracer import Tracer, TraceEntry, _preview


@pytest.fixture
def tracer() -> Tracer:
    return Tracer()


def test_record_adds_entry(tracer):
    tracer.record("DB_PASS", "secret/db", "hunter2")
    assert len(tracer.entries()) == 1


def test_resolved_entry_when_value_present(tracer):
    entry = tracer.record("DB_PASS", "secret/db", "hunter2")
    assert entry.resolved is True


def test_unresolved_entry_when_value_none(tracer):
    entry = tracer.record("MISSING", "secret/db", None)
    assert entry.resolved is False


def test_entry_key_and_path_are_stored(tracer):
    entry = tracer.record("API_KEY", "secret/api", "abc123")
    assert entry.key == "API_KEY"
    assert entry.path == "secret/api"


def test_entry_timestamp_is_iso_format(tracer):
    entry = tracer.record("X", "p", "v")
    # should not raise
    from datetime import datetime
    datetime.fromisoformat(entry.timestamp)


def test_entry_note_is_stored(tracer):
    entry = tracer.record("X", "p", "v", note="from cache")
    assert entry.note == "from cache"


def test_resolved_filters_only_resolved(tracer):
    tracer.record("A", "p", "val")
    tracer.record("B", "p", None)
    assert len(tracer.resolved()) == 1
    assert tracer.resolved()[0].key == "A"


def test_unresolved_filters_only_unresolved(tracer):
    tracer.record("A", "p", "val")
    tracer.record("B", "p", None)
    assert len(tracer.unresolved()) == 1
    assert tracer.unresolved()[0].key == "B"


def test_summary_counts_are_correct(tracer):
    tracer.record("A", "p", "v")
    tracer.record("B", "p", None)
    tracer.record("C", "p", "v2")
    s = tracer.summary()
    assert s["total"] == 3
    assert s["resolved"] == 2
    assert s["unresolved"] == 1


def test_clear_removes_all_entries(tracer):
    tracer.record("A", "p", "v")
    tracer.clear()
    assert tracer.entries() == []


def test_preview_masks_short_value():
    assert _preview("abc") == "***"


def test_preview_masks_long_value_with_ellipsis():
    result = _preview("averylongpassword")
    assert result == "******..."


def test_preview_none_returns_none_marker():
    assert _preview(None) == "<none>"


def test_to_dict_contains_all_keys(tracer):
    entry = tracer.record("K", "path/to", "val", note="hi")
    d = entry.to_dict()
    assert set(d.keys()) == {"key", "path", "resolved", "value_preview", "timestamp", "note"}
