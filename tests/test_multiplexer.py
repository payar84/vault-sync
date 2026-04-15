"""Tests for vault_sync.multiplexer."""
from __future__ import annotations

from typing import Dict, Optional

import pytest

from vault_sync.multiplexer import MultiplexConfig, MultiplexResult, multiplex


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_fetcher(store: Dict[str, Optional[Dict[str, str]]]):
    def fetcher(path: str) -> Optional[Dict[str, str]]:
        if path not in store:
            raise KeyError(f"unknown path: {path}")
        return store[path]
    return fetcher


# ---------------------------------------------------------------------------
# config validation
# ---------------------------------------------------------------------------

def test_config_rejects_empty_paths():
    with pytest.raises(ValueError, match="paths must contain at least one entry"):
        MultiplexConfig(paths=[]).validate()


def test_config_rejects_blank_path_entry():
    with pytest.raises(ValueError, match="invalid path entry"):
        MultiplexConfig(paths=["  "]).validate()


def test_config_accepts_valid_paths():
    cfg = MultiplexConfig(paths=["secret/a", "secret/b"])
    cfg.validate()  # should not raise


# ---------------------------------------------------------------------------
# multiplex behaviour
# ---------------------------------------------------------------------------

def test_reads_single_path():
    fetcher = _make_fetcher({"secret/a": {"KEY": "val"}})
    result = multiplex(MultiplexConfig(paths=["secret/a"]), fetcher)
    assert result.ok
    assert result.secrets == {"KEY": "val"}
    assert result.paths_read == ["secret/a"]


def test_merges_multiple_paths():
    fetcher = _make_fetcher({
        "secret/a": {"A": "1"},
        "secret/b": {"B": "2"},
    })
    result = multiplex(MultiplexConfig(paths=["secret/a", "secret/b"]), fetcher)
    assert result.secrets == {"A": "1", "B": "2"}
    assert len(result.paths_read) == 2


def test_deduplication_keeps_first_value():
    fetcher = _make_fetcher({
        "secret/a": {"KEY": "first"},
        "secret/b": {"KEY": "second"},
    })
    result = multiplex(MultiplexConfig(paths=["secret/a", "secret/b"], deduplicate=True), fetcher)
    assert result.secrets["KEY"] == "first"


def test_no_deduplication_overwrites_value():
    fetcher = _make_fetcher({
        "secret/a": {"KEY": "first"},
        "secret/b": {"KEY": "second"},
    })
    result = multiplex(MultiplexConfig(paths=["secret/a", "secret/b"], deduplicate=False), fetcher)
    assert result.secrets["KEY"] == "second"


def test_error_is_recorded_and_continues():
    fetcher = _make_fetcher({"secret/b": {"B": "2"}})
    result = multiplex(MultiplexConfig(paths=["secret/missing", "secret/b"]), fetcher)
    assert not result.ok
    assert "secret/missing" in result.errors
    assert result.secrets == {"B": "2"}


def test_stop_on_error_halts_processing():
    fetcher = _make_fetcher({"secret/b": {"B": "2"}})
    result = multiplex(
        MultiplexConfig(paths=["secret/missing", "secret/b"], stop_on_error=True),
        fetcher,
    )
    assert not result.ok
    assert result.secrets == {}
    assert result.paths_read == []


def test_none_data_is_treated_as_error():
    fetcher = _make_fetcher({"secret/a": None})
    result = multiplex(MultiplexConfig(paths=["secret/a"]), fetcher)
    assert not result.ok
    assert "secret/a" in result.errors


def test_total_keys_reflects_merged_count():
    fetcher = _make_fetcher({
        "secret/a": {"X": "1", "Y": "2"},
        "secret/b": {"Z": "3"},
    })
    result = multiplex(MultiplexConfig(paths=["secret/a", "secret/b"]), fetcher)
    assert result.total_keys == 3
