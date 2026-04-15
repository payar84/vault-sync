"""Tests for vault_sync.ledger and vault_sync.ledger_command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vault_sync.ledger import Ledger, LedgerEntry
from vault_sync.ledger_command import build_ledger_parser, run_ledger_command


@pytest.fixture
def ledger_file(tmp_path: Path) -> Path:
    return tmp_path / "test_ledger.json"


@pytest.fixture
def ledger() -> Ledger:
    return Ledger()


def test_record_adds_entry(ledger: Ledger) -> None:
    entry = ledger.record("DB_PASSWORD", "secret/db", ".env")
    assert entry.key == "DB_PASSWORD"
    assert entry.path == "secret/db"
    assert entry.env_file == ".env"


def test_record_stores_synced_at(ledger: Ledger) -> None:
    entry = ledger.record("API_KEY", "secret/api", ".env")
    assert "T" in entry.synced_at  # ISO format


def test_record_stores_checksum(ledger: Ledger) -> None:
    entry = ledger.record("TOKEN", "secret/token", ".env", checksum="abc123")
    assert entry.checksum == "abc123"


def test_get_returns_none_when_missing(ledger: Ledger) -> None:
    assert ledger.get("MISSING") is None


def test_get_returns_entry_after_record(ledger: Ledger) -> None:
    ledger.record("FOO", "secret/foo", ".env")
    assert ledger.get("FOO") is not None


def test_all_entries_sorted_by_key(ledger: Ledger) -> None:
    ledger.record("Z_KEY", "secret/z", ".env")
    ledger.record("A_KEY", "secret/a", ".env")
    keys = [e.key for e in ledger.all_entries()]
    assert keys == sorted(keys)


def test_remove_returns_true_when_present(ledger: Ledger) -> None:
    ledger.record("REMOVE_ME", "secret/x", ".env")
    assert ledger.remove("REMOVE_ME") is True
    assert ledger.get("REMOVE_ME") is None


def test_remove_returns_false_when_absent(ledger: Ledger) -> None:
    assert ledger.remove("GHOST") is False


def test_save_and_load_roundtrip(ledger: Ledger, ledger_file: Path) -> None:
    ledger.record("DB_HOST", "secret/db", ".env", checksum="deadbeef")
    ledger.save(ledger_file)
    loaded = Ledger.load(ledger_file)
    entry = loaded.get("DB_HOST")
    assert entry is not None
    assert entry.path == "secret/db"
    assert entry.checksum == "deadbeef"


def test_load_returns_empty_when_file_missing(tmp_path: Path) -> None:
    ledger = Ledger.load(tmp_path / "nonexistent.json")
    assert ledger.all_entries() == []


def test_to_dict_contains_all_keys() -> None:
    entry = LedgerEntry("K", "p/k", ".env", "2024-01-01T00:00:00+00:00", "abc")
    d = entry.to_dict()
    assert set(d.keys()) == {"key", "path", "env_file", "synced_at", "checksum"}


def test_from_dict_roundtrip() -> None:
    original = LedgerEntry("K", "p/k", ".env", "2024-01-01T00:00:00+00:00", "abc")
    restored = LedgerEntry.from_dict(original.to_dict())
    assert restored.key == original.key
    assert restored.checksum == original.checksum


# --- command tests ---

def _run(args: list, ledger_file: Path) -> int:
    parser = build_ledger_parser()
    parsed = parser.parse_args(["--ledger-file", str(ledger_file)] + args)
    return run_ledger_command(parsed)


def test_list_empty_returns_zero(tmp_path: Path) -> None:
    lf = tmp_path / "ledger.json"
    assert _run(["list"], lf) == 0


def test_list_shows_entries(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    lf = tmp_path / "ledger.json"
    ledger = Ledger()
    ledger.record("MY_KEY", "secret/mine", ".env")
    ledger.save(lf)
    assert _run(["list"], lf) == 0
    out = capsys.readouterr().out
    assert "MY_KEY" in out


def test_remove_existing_key_returns_zero(tmp_path: Path) -> None:
    lf = tmp_path / "ledger.json"
    ledger = Ledger()
    ledger.record("DEL_KEY", "secret/del", ".env")
    ledger.save(lf)
    assert _run(["remove", "DEL_KEY"], lf) == 0


def test_remove_missing_key_returns_one(tmp_path: Path) -> None:
    lf = tmp_path / "ledger.json"
    assert _run(["remove", "NOPE"], lf) == 1


def test_show_existing_key_returns_zero(tmp_path: Path) -> None:
    lf = tmp_path / "ledger.json"
    ledger = Ledger()
    ledger.record("SHOW_KEY", "secret/show", ".env")
    ledger.save(lf)
    assert _run(["show", "SHOW_KEY"], lf) == 0


def test_show_missing_key_returns_one(tmp_path: Path) -> None:
    lf = tmp_path / "ledger.json"
    assert _run(["show", "MISSING"], lf) == 1
