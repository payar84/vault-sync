"""Tests for vault_sync.watermark."""
import json
from pathlib import Path

import pytest

from vault_sync.watermark import Watermark, WatermarkConfig, WatermarkEntry


@pytest.fixture
def wm():
    return Watermark(config=WatermarkConfig(max_entries=100))


def test_config_rejects_zero_max_entries():
    with pytest.raises(ValueError, match="max_entries"):
        WatermarkConfig(max_entries=0).validate()


def test_config_rejects_negative_max_entries():
    with pytest.raises(ValueError):
        WatermarkConfig(max_entries=-5).validate()


def test_config_accepts_valid_values():
    WatermarkConfig(max_entries=10).validate()


def test_record_returns_entry(wm):
    entry = wm.record("secret/app", 5)
    assert isinstance(entry, WatermarkEntry)
    assert entry.path == "secret/app"
    assert entry.key_count == 5


def test_latest_returns_most_recent(wm):
    wm.record("secret/app", 3)
    wm.record("secret/app", 7)
    latest = wm.latest("secret/app")
    assert latest.key_count == 7


def test_latest_returns_none_for_unknown_path(wm):
    assert wm.latest("secret/missing") is None


def test_peak_returns_highest_key_count(wm):
    wm.record("secret/app", 3)
    wm.record("secret/app", 10)
    wm.record("secret/app", 6)
    peak = wm.peak("secret/app")
    assert peak.key_count == 10


def test_peak_returns_none_for_unknown_path(wm):
    assert wm.peak("secret/unknown") is None


def test_all_paths_returns_unique_paths(wm):
    wm.record("secret/a", 1)
    wm.record("secret/b", 2)
    wm.record("secret/a", 3)
    paths = wm.all_paths()
    assert sorted(paths) == ["secret/a", "secret/b"]


def test_max_entries_trims_oldest(tmp_path):
    wm = Watermark(config=WatermarkConfig(max_entries=3))
    for i in range(5):
        wm.record("secret/app", i)
    assert len(wm._entries) == 3
    assert wm._entries[0].key_count == 2


def test_entry_to_dict_contains_all_keys():
    entry = WatermarkEntry(path="secret/x", key_count=4)
    d = entry.to_dict()
    assert "path" in d
    assert "key_count" in d
    assert "synced_at" in d


def test_entry_roundtrip_from_dict():
    entry = WatermarkEntry(path="secret/x", key_count=4)
    restored = WatermarkEntry.from_dict(entry.to_dict())
    assert restored.path == entry.path
    assert restored.key_count == entry.key_count
    assert restored.synced_at == entry.synced_at


def test_save_and_load_roundtrip(tmp_path, wm):
    wm.record("secret/app", 5)
    wm.record("secret/db", 3)
    store = tmp_path / "wm.json"
    wm.save(store)
    wm2 = Watermark()
    wm2.load(store)
    assert wm2.latest("secret/app").key_count == 5
    assert wm2.latest("secret/db").key_count == 3


def test_load_missing_file_does_not_raise(tmp_path, wm):
    wm.load(tmp_path / "nonexistent.json")  # should not raise
    assert wm.all_paths() == []
