"""Tests for vault_sync.diff module."""

import pytest
from vault_sync.diff import ChangeType, SecretChange, compute_diff, format_diff_summary


CURRENT = {
    "DB_HOST": "localhost",
    "DB_PASS": "old_pass",
    "OBSOLETE_KEY": "to_be_removed",
}

INCOMING = {
    "DB_HOST": "localhost",
    "DB_PASS": "new_pass",
    "NEW_KEY": "shiny",
}


def test_added_key_is_detected():
    changes = compute_diff(CURRENT, INCOMING)
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].key == "NEW_KEY"
    assert added[0].new_value == "shiny"
    assert added[0].old_value is None


def test_removed_key_is_detected():
    changes = compute_diff(CURRENT, INCOMING)
    removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].key == "OBSOLETE_KEY"
    assert removed[0].old_value == "to_be_removed"
    assert removed[0].new_value is None


def test_updated_key_is_detected():
    changes = compute_diff(CURRENT, INCOMING)
    updated = [c for c in changes if c.change_type == ChangeType.UPDATED]
    assert len(updated) == 1
    assert updated[0].key == "DB_PASS"
    assert updated[0].old_value == "old_pass"
    assert updated[0].new_value == "new_pass"


def test_unchanged_key_is_detected():
    changes = compute_diff(CURRENT, INCOMING)
    unchanged = [c for c in changes if c.change_type == ChangeType.UNCHANGED]
    assert len(unchanged) == 1
    assert unchanged[0].key == "DB_HOST"


def test_results_are_sorted_by_key():
    changes = compute_diff(CURRENT, INCOMING)
    keys = [c.key for c in changes]
    assert keys == sorted(keys)


def test_empty_diffs():
    changes = compute_diff({}, {})
    assert changes == []


def test_format_diff_summary_shows_changes():
    changes = compute_diff(CURRENT, INCOMING)
    summary = format_diff_summary(changes)
    assert "[+] NEW_KEY" in summary
    assert "[-] OBSOLETE_KEY" in summary
    assert "[~] DB_PASS" in summary
    assert "DB_HOST" not in summary


def test_format_diff_summary_no_changes():
    state = {"KEY": "value"}
    changes = compute_diff(state, state)
    summary = format_diff_summary(changes)
    assert summary == "No changes detected."


def test_secret_change_repr_added():
    change = SecretChange(key="FOO", change_type=ChangeType.ADDED, new_value="bar")
    assert repr(change) == "[+] FOO"


def test_secret_change_repr_removed():
    change = SecretChange(key="FOO", change_type=ChangeType.REMOVED, old_value="bar")
    assert repr(change) == "[-] FOO"
