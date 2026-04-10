"""Tests for vault_sync.snapshot_manager."""
import pytest

from vault_sync.snapshot_manager import SnapshotManager


@pytest.fixture()
def manager(tmp_path):
    return SnapshotManager(directory=tmp_path / "snaps", max_snapshots=3)


@pytest.fixture()
def secrets():
    return {"KEY_A": "alpha", "KEY_B": "beta"}


def test_capture_returns_snapshot(manager, secrets):
    snap = manager.capture(secrets, label="test")
    assert snap.secrets == secrets
    assert snap.label == "test"


def test_latest_is_none_when_empty(manager):
    assert manager.latest() is None


def test_latest_returns_most_recent(manager, secrets):
    manager.capture({"K": "v1"}, label="first")
    manager.capture({"K": "v2"}, label="second")
    latest = manager.latest()
    assert latest.label == "second"


def test_history_sorted_oldest_first(manager):
    manager.capture({"K": "v1"})
    manager.capture({"K": "v2"})
    history = manager.history()
    assert history[0].timestamp <= history[1].timestamp


def test_prune_keeps_max_snapshots(manager, secrets):
    for i in range(5):
        manager.capture({"K": str(i)})
    remaining = list((manager.directory).glob("snapshot_*.json"))
    assert len(remaining) == 3


def test_diff_latest_returns_none_without_baseline(manager, secrets):
    result = manager.diff_latest(secrets)
    assert result is None


def test_diff_latest_detects_change(manager, secrets):
    manager.capture(secrets)
    updated = {**secrets, "KEY_A": "changed"}
    diff = manager.diff_latest(updated)
    assert "KEY_A" in diff
    assert diff["KEY_A"] == ("alpha", "changed")


def test_diff_latest_empty_when_unchanged(manager, secrets):
    manager.capture(secrets)
    diff = manager.diff_latest(dict(secrets))
    assert diff == {}


def test_manager_rejects_zero_max_snapshots(tmp_path):
    with pytest.raises(ValueError, match="max_snapshots"):
        SnapshotManager(directory=tmp_path, max_snapshots=0)
