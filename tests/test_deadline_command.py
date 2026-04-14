"""Tests for vault_sync.deadline_command."""
from __future__ import annotations

import argparse

import pytest

from vault_sync.deadline_command import (
    build_deadline_parser,
    run_deadline_command,
    add_deadline_subcommand,
)


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    return build_deadline_parser()


def _run(args: list[str]) -> int:
    p = build_deadline_parser()
    ns = p.parse_args(args)
    return run_deadline_command(ns)


def test_default_run_returns_zero():
    assert _run([]) == 0


def test_valid_config_returns_zero():
    assert _run(["--max-seconds", "10", "--warn-at", "0.7"]) == 0


def test_zero_max_seconds_returns_one():
    assert _run(["--max-seconds", "0"]) == 1


def test_negative_max_seconds_returns_one():
    assert _run(["--max-seconds", "-5"]) == 1


def test_warn_at_zero_returns_one():
    assert _run(["--max-seconds", "10", "--warn-at", "0"]) == 1


def test_warn_at_one_returns_one():
    assert _run(["--max-seconds", "10", "--warn-at", "1.0"]) == 1


def test_add_deadline_subcommand_registers(capsys):
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_deadline_subcommand(sub)
    ns = root.parse_args(["deadline", "--max-seconds", "5"])
    assert hasattr(ns, "func")


def test_output_contains_status_repr(capsys):
    _run(["--max-seconds", "30"])
    captured = capsys.readouterr()
    assert "DeadlineStatus" in captured.out


def test_output_contains_remaining(capsys):
    _run(["--max-seconds", "30"])
    captured = capsys.readouterr()
    assert "remaining" in captured.out
