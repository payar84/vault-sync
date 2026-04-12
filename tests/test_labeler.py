"""Tests for vault_sync.labeler."""

import pytest

from vault_sync.labeler import LabelRegistry, LabelSet


# ---------------------------------------------------------------------------
# LabelSet
# ---------------------------------------------------------------------------


def test_labelset_normalises_path():
    ls = LabelSet(path="/secret/app/", labels=[])
    assert ls.path == "secret/app"


def test_labelset_normalises_labels_to_lowercase():
    ls = LabelSet(path="secret/app", labels=["Prod", "CRITICAL"])
    assert "prod" in ls.labels
    assert "critical" in ls.labels


def test_labelset_strips_blank_labels():
    ls = LabelSet(path="secret/app", labels=["  ", "prod", ""])
    assert ls.labels == ["prod"]


def test_labelset_has_returns_true_for_present_label():
    ls = LabelSet(path="secret/app", labels=["staging"])
    assert ls.has("STAGING") is True


def test_labelset_has_returns_false_for_absent_label():
    ls = LabelSet(path="secret/app", labels=["staging"])
    assert ls.has("prod") is False


def test_labelset_add_appends_new_label():
    ls = LabelSet(path="secret/app", labels=[])
    ls.add("prod")
    assert ls.has("prod") is True


def test_labelset_add_is_idempotent():
    ls = LabelSet(path="secret/app", labels=["prod"])
    ls.add("prod")
    assert ls.labels.count("prod") == 1


def test_labelset_remove_returns_true_when_present():
    ls = LabelSet(path="secret/app", labels=["prod"])
    result = ls.remove("prod")
    assert result is True
    assert ls.has("prod") is False


def test_labelset_remove_returns_false_when_absent():
    ls = LabelSet(path="secret/app", labels=[])
    assert ls.remove("prod") is False


def test_labelset_to_dict_sorts_labels():
    ls = LabelSet(path="secret/app", labels=["zebra", "alpha"])
    d = ls.to_dict()
    assert d["labels"] == ["alpha", "zebra"]


# ---------------------------------------------------------------------------
# LabelRegistry
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry() -> LabelRegistry:
    reg = LabelRegistry()
    reg.register("secret/app", ["prod", "critical"])
    reg.register("secret/db", ["prod", "database"])
    reg.register("secret/dev", ["staging"])
    return reg


def test_registry_get_returns_labelset(registry: LabelRegistry):
    ls = registry.get("secret/app")
    assert ls is not None
    assert ls.has("prod")


def test_registry_get_strips_slashes(registry: LabelRegistry):
    ls = registry.get("/secret/app/")
    assert ls is not None


def test_registry_get_returns_none_for_unknown(registry: LabelRegistry):
    assert registry.get("secret/missing") is None


def test_registry_find_by_label_returns_matching(registry: LabelRegistry):
    results = registry.find_by_label("prod")
    paths = [ls.path for ls in results]
    assert "secret/app" in paths
    assert "secret/db" in paths
    assert "secret/dev" not in paths


def test_registry_find_by_label_empty_when_none_match(registry: LabelRegistry):
    assert registry.find_by_label("nonexistent") == []


def test_registry_all_labels_are_sorted_and_unique(registry: LabelRegistry):
    labels = registry.all_labels()
    assert labels == sorted(set(labels))
    assert "prod" in labels
    assert "database" in labels


def test_registry_to_dict_keys_are_sorted(registry: LabelRegistry):
    d = registry.to_dict()
    assert list(d.keys()) == sorted(d.keys())
