"""Tests for vault_sync.pruner."""

from __future__ import annotations

import pytest

from vault_sync.pruner import PruneResult, compute_stale_keys, prune_secrets


# ---------------------------------------------------------------------------
# compute_stale_keys
# ---------------------------------------------------------------------------

def test_stale_keys_returns_local_only_keys():
    local = {"A": "1", "B": "2", "C": "3"}
    vault = {"A": "1", "C": "3"}
    assert compute_stale_keys(local, vault) == {"B"}


def test_stale_keys_empty_when_vault_is_superset():
    local = {"A": "1"}
    vault = {"A": "1", "B": "2"}
    assert compute_stale_keys(local, vault) == set()


def test_stale_keys_all_when_vault_is_empty():
    local = {"A": "1", "B": "2"}
    vault = {}
    assert compute_stale_keys(local, vault) == {"A", "B"}


def test_stale_keys_empty_when_both_empty():
    assert compute_stale_keys({}, {}) == set()


# ---------------------------------------------------------------------------
# prune_secrets
# ---------------------------------------------------------------------------

def test_prune_removes_stale_keys():
    local = {"A": "1", "B": "2", "C": "3"}
    vault = {"A": "1", "C": "3"}
    result = prune_secrets(local, vault)
    assert "B" not in local
    assert result.removed == ["B"]


def test_prune_keeps_active_keys():
    local = {"A": "1", "B": "2"}
    vault = {"A": "1", "B": "2"}
    result = prune_secrets(local, vault)
    assert result.removed == []
    assert set(result.kept) == {"A", "B"}


def test_prune_dry_run_does_not_mutate():
    local = {"A": "1", "B": "stale"}
    vault = {"A": "1"}
    result = prune_secrets(local, vault, dry_run=True)
    assert "B" in local  # not removed
    assert result.removed == ["B"]


def test_prune_result_total_removed():
    result = PruneResult(removed=["X", "Y"], kept=["Z"])
    assert result.total_removed == 2


def test_prune_result_total_kept():
    result = PruneResult(removed=["X"], kept=["Y", "Z"])
    assert result.total_kept == 2


def test_prune_result_ok_is_always_true():
    assert PruneResult().ok is True


def test_prune_removed_list_is_sorted():
    local = {"C": "3", "A": "1", "B": "2"}
    vault = {}
    result = prune_secrets(local, vault, dry_run=True)
    assert result.removed == ["A", "B", "C"]


def test_prune_kept_list_is_sorted():
    local = {"C": "3", "A": "1", "B": "2"}
    vault = {"C": "3", "A": "1", "B": "2"}
    result = prune_secrets(local, vault)
    assert result.kept == ["A", "B", "C"]
