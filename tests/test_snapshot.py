"""Tests for vault_sync.snapshot."""
import time
from pathlib import Path

import pytest

from vault_sync.snapshot import (
    Snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
    take_snapshot,
)


@pytest.fixture()
def sample_secrets():
    return {"DB_HOST": "localhost", "DB_PASS": "secret", "API_KEY": "abc123"}


@pytest.fixture()
def snapshot(sample_secrets):
    return take_snapshot(sample_secrets, label="initial")


def test_take_snapshot_stores_secrets(sample_secrets, snapshot):
    assert snapshot.secrets == sample_secrets


def test_take_snapshot_sets_label(snapshot):
    assert snapshot.label == "initial"


def test_take_snapshot_sets_timestamp(snapshot):
    assert snapshot.timestamp == pytest.approx(time.time(), abs=2)


def test_to_dict_contains_all_fields(snapshot):
    d = snapshot.to_dict()
    assert "timestamp" in d
    assert "secrets" in d
    assert "label" in d


def test_from_dict_roundtrip(snapshot):
    restored = Snapshot.from_dict(snapshot.to_dict())
    assert restored.secrets == snapshot.secrets
    assert restored.label == snapshot.label
    assert restored.timestamp == snapshot.timestamp


def test_diff_detects_added_key(sample_secrets):
    s1 = take_snapshot(sample_secrets)
    new_secrets = {**sample_secrets, "NEW_KEY": "new_value"}
    s2 = take_snapshot(new_secrets)
    diff = s1.diff(s2)
    assert "NEW_KEY" in diff
    assert diff["NEW_KEY"] == (None, "new_value")


def test_diff_detects_removed_key(sample_secrets):
    s1 = take_snapshot(sample_secrets)
    reduced = {k: v for k, v in sample_secrets.items() if k != "API_KEY"}
    s2 = take_snapshot(reduced)
    diff = s1.diff(s2)
    assert "API_KEY" in diff
    assert diff["API_KEY"] == ("abc123", None)


def test_diff_detects_changed_value(sample_secrets):
    s1 = take_snapshot(sample_secrets)
    updated = {**sample_secrets, "DB_PASS": "new_secret"}
    s2 = take_snapshot(updated)
    diff = s1.diff(s2)
    assert diff["DB_PASS"] == ("secret", "new_secret")


def test_diff_empty_when_identical(sample_secrets):
    s1 = take_snapshot(sample_secrets)
    s2 = take_snapshot(dict(sample_secrets))
    assert s1.diff(s2) == {}


def test_save_and_load_snapshot(tmp_path, snapshot):
    path = save_snapshot(snapshot, tmp_path)
    assert path.exists()
    loaded = load_snapshot(path)
    assert loaded.secrets == snapshot.secrets
    assert loaded.label == snapshot.label


def test_list_snapshots_returns_sorted(tmp_path, sample_secrets):
    s1 = Snapshot(timestamp=1000.0, secrets=sample_secrets)
    s2 = Snapshot(timestamp=2000.0, secrets=sample_secrets)
    save_snapshot(s2, tmp_path)
    save_snapshot(s1, tmp_path)
    snapshots = list_snapshots(tmp_path)
    assert snapshots[0].timestamp < snapshots[1].timestamp


def test_list_snapshots_empty_when_dir_missing(tmp_path):
    result = list_snapshots(tmp_path / "nonexistent")
    assert result == []
