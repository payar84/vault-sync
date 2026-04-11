"""Tests for vault_sync.pin and vault_sync.pin_command."""
import json
from pathlib import Path

import pytest

from vault_sync.pin import PinStore, _sha256
from vault_sync.pin_command import build_pin_parser, run_pin_command


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    return tmp_path / "pins.json"


@pytest.fixture()
def store(store_file: Path) -> PinStore:
    return PinStore(store_file)


# ---------------------------------------------------------------------------
# PinStore unit tests
# ---------------------------------------------------------------------------

def test_pin_creates_entry(store: PinStore) -> None:
    entry = store.pin("DB_PASSWORD", "secret/db", "s3cr3t")
    assert entry.key == "DB_PASSWORD"
    assert entry.hash == _sha256("s3cr3t")


def test_get_returns_none_when_missing(store: PinStore) -> None:
    assert store.get("MISSING") is None


def test_get_returns_entry_after_pin(store: PinStore) -> None:
    store.pin("API_KEY", "secret/api", "tok123")
    assert store.get("API_KEY") is not None


def test_matches_correct_value(store: PinStore) -> None:
    store.pin("TOKEN", "secret/svc", "abc")
    assert store.check("TOKEN", "abc") is True


def test_does_not_match_wrong_value(store: PinStore) -> None:
    store.pin("TOKEN", "secret/svc", "abc")
    assert store.check("TOKEN", "xyz") is False


def test_check_returns_none_for_unpinned(store: PinStore) -> None:
    assert store.check("UNKNOWN", "value") is None


def test_remove_returns_true_when_present(store: PinStore) -> None:
    store.pin("K", "p", "v")
    assert store.remove("K") is True
    assert store.get("K") is None


def test_remove_returns_false_when_absent(store: PinStore) -> None:
    assert store.remove("NOPE") is False


def test_save_and_reload(store: PinStore, store_file: Path) -> None:
    store.pin("DB_PASS", "secret/db", "hunter2")
    store.save()
    reloaded = PinStore(store_file)
    entry = reloaded.get("DB_PASS")
    assert entry is not None
    assert entry.matches("hunter2")


# ---------------------------------------------------------------------------
# pin_command tests
# ---------------------------------------------------------------------------

def _run(args_list, store_file):
    parser = build_pin_parser()
    args = parser.parse_args(["--store", str(store_file)] + args_list)
    return run_pin_command(args)


def test_add_command_returns_zero(store_file, capsys):
    rc = _run(["add", "MY_KEY", "secret/svc", "value1"], store_file)
    assert rc == 0
    assert store_file.exists()


def test_list_shows_pinned_key(store_file, capsys):
    _run(["add", "MY_KEY", "secret/svc", "value1"], store_file)
    rc = _run(["list"], store_file)
    assert rc == 0
    out = capsys.readouterr().out
    assert "MY_KEY" in out


def test_check_passes_for_correct_value(store_file):
    _run(["add", "X", "p", "correct"], store_file)
    rc = _run(["check", "X", "correct"], store_file)
    assert rc == 0


def test_check_fails_for_wrong_value(store_file):
    _run(["add", "X", "p", "correct"], store_file)
    rc = _run(["check", "X", "wrong"], store_file)
    assert rc == 2


def test_remove_command(store_file):
    _run(["add", "X", "p", "v"], store_file)
    rc = _run(["remove", "X"], store_file)
    assert rc == 0
    rc2 = _run(["remove", "X"], store_file)
    assert rc2 == 1
