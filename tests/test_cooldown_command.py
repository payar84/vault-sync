"""Tests for vault_sync.cooldown_command."""
from __future__ import annotations

import argparse
import pytest

from vault_sync.cooldown_command import build_cooldown_parser, run_cooldown_command


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    return build_cooldown_parser()


def _run(parser: argparse.ArgumentParser, argv: list) -> int:
    args = parser.parse_args(argv)
    return run_cooldown_command(args)


def test_check_untracked_path_returns_zero(parser):
    # Path has never been synced — should be ready (exit 0)
    result = _run(parser, ["check", "secret/app", "--interval", "30"])
    assert result == 0


def test_check_invalid_interval_returns_one(parser):
    result = _run(parser, ["check", "secret/app", "--interval", "0"])
    assert result == 1


def test_demo_returns_zero(parser):
    result = _run(parser, ["demo", "--interval", "5"])
    assert result == 0


def test_demo_invalid_interval_returns_one(parser):
    result = _run(parser, ["demo", "--interval", "-1"])
    assert result == 1


def test_check_prints_status(parser, capsys):
    _run(parser, ["check", "secret/db", "--interval", "60"])
    captured = capsys.readouterr()
    assert "secret/db" in captured.out
