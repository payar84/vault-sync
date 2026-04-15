"""Tests for vault_sync.jitter_command."""
from __future__ import annotations

import argparse

import pytest

from vault_sync.jitter_command import build_jitter_parser, run_jitter_command


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    return build_jitter_parser()


def _run(args: list, capsys) -> int:
    p = build_jitter_parser()
    ns = p.parse_args(args)
    code = run_jitter_command(ns)
    return code


def test_default_run_returns_zero(capsys):
    assert _run([], capsys) == 0


def test_none_strategy_returns_zero(capsys):
    assert _run(["--strategy", "none"], capsys) == 0


def test_equal_strategy_returns_zero(capsys):
    assert _run(["--strategy", "equal", "--base-delay", "2.0"], capsys) == 0


def test_decorrelated_strategy_returns_zero(capsys):
    assert _run(["--strategy", "decorrelated", "--seed", "42"], capsys) == 0


def test_output_contains_strategy(capsys):
    _run(["--strategy", "full", "--seed", "1"], capsys)
    out = capsys.readouterr().out
    assert "full" in out


def test_output_contains_base_delay(capsys):
    _run(["--base-delay", "3.5", "--seed", "0"], capsys)
    out = capsys.readouterr().out
    assert "3.500" in out


def test_iterations_controls_sample_count(capsys):
    _run(["--iterations", "3", "--seed", "0"], capsys)
    out = capsys.readouterr().out
    assert "[01]" in out
    assert "[03]" in out
    assert "[04]" not in out


def test_invalid_max_delay_returns_one(capsys):
    p = build_jitter_parser()
    ns = p.parse_args(["--max-delay", "0.0"])
    assert run_jitter_command(ns) == 1


def test_invalid_min_greater_than_max_returns_one(capsys):
    p = build_jitter_parser()
    ns = p.parse_args(["--min-delay", "20.0", "--max-delay", "5.0"])
    assert run_jitter_command(ns) == 1


def test_seed_produces_reproducible_output(capsys):
    _run(["--seed", "77", "--iterations", "5"], capsys)
    out1 = capsys.readouterr().out
    _run(["--seed", "77", "--iterations", "5"], capsys)
    out2 = capsys.readouterr().out
    assert out1 == out2
