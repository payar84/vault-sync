"""Tests for vault_sync.checkpoint."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from vault_sync.checkpoint import Checkpoint, CheckpointConfig, CheckpointEntry


@pytest.fixture
def config() -> CheckpointConfig:
    return CheckpointConfig(max_entries=5, ttl_seconds=3600.0)


@pytest.fixture
def cp(config: CheckpointConfig) -> Checkpoint:
    return Checkpoint(config=config)


def test_config_rejects_zero_max_entries():
    with pytest.raises(ValueError, match="max_entries"):
        CheckpointConfig(max_entries=0).validate()


def test_config_rejects_negative_max_entries():
    with pytest.raises(ValueError, match="max_entries"):
        CheckpointConfig(max_entries=-1).validate()


def test_config_rejects_zero_ttl():
    with pytest.raises(ValueError, match="ttl_seconds"):
        CheckpointConfig(ttl_seconds=0).validate()


def test_config_accepts_valid_values():
    cfg = CheckpointConfig(max_entries=10, ttl_seconds=60.0)
    cfg.validate()  # should not raise


def test_record_returns_entry(cp: Checkpoint):
    entry = cp.record("secret/app", key_count=3, checksum="abc")
    assert isinstance(entry, CheckpointEntry)
    assert entry.path == "secret/app"
    assert entry.key_count == 3
    assert entry.checksum == "abc"


def test_get_returns_recorded_entry(cp: Checkpoint):
    cp.record("secret/app", 3, "abc")
    result = cp.get("secret/app")
    assert result is not None
    assert result.key_count == 3


def test_get_returns_none_when_missing(cp: Checkpoint):
    assert cp.get("secret/missing") is None


def test_expired_entry_returns_none():
    cfg = CheckpointConfig(max_entries=10, ttl_seconds=0.001)
    cp = Checkpoint(config=cfg)
    cp.record("secret/x", 1, "hash")
    time.sleep(0.01)
    assert cp.get("secret/x") is None


def test_eviction_keeps_most_recent():
    cfg = CheckpointConfig(max_entries=3, ttl_seconds=3600)
    cp = Checkpoint(config=cfg)
    for i in range(5):
        cp.record(f"secret/path{i}", i, f"hash{i}")
    assert len(cp._entries) == 3


def test_all_paths_returns_recorded_paths(cp: Checkpoint):
    cp.record("a/b", 1, "x")
    cp.record("c/d", 2, "y")
    paths = cp.all_paths()
    assert "a/b" in paths
    assert "c/d" in paths


def test_save_and_load_roundtrip(tmp_path: Path, cp: Checkpoint):
    cp.record("secret/app", 4, "deadbeef")
    fpath = tmp_path / "cp.json"
    cp.save(fpath)
    cp2 = Checkpoint(config=cp.config)
    cp2.load(fpath)
    entry = cp2.get("secret/app")
    assert entry is not None
    assert entry.key_count == 4
    assert entry.checksum == "deadbeef"


def test_load_missing_file_is_noop(tmp_path: Path, cp: Checkpoint):
    cp.load(tmp_path / "nonexistent.json")  # should not raise
    assert cp.all_paths() == []


def test_to_dict_contains_expected_keys():
    entry = CheckpointEntry(path="p", synced_at=1000.0, key_count=2, checksum="abc")
    d = entry.to_dict()
    assert set(d.keys()) == {"path", "synced_at", "key_count", "checksum"}


def test_from_dict_roundtrip():
    entry = CheckpointEntry(path="p", synced_at=1234.5, key_count=7, checksum="xyz")
    restored = CheckpointEntry.from_dict(entry.to_dict())
    assert restored.path == entry.path
    assert restored.key_count == entry.key_count
    assert restored.checksum == entry.checksum
