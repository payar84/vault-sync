"""Tests for vault_sync.gateway_command"""
from __future__ import annotations

import argparse
import pytest

from vault_sync.gateway_command import build_gateway_parser, run_gateway_command


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    return build_gateway_parser()


def _run(parser: argparse.ArgumentParser, argv: list) -> int:
    args = parser.parse_args(argv)
    return run_gateway_command(args)


def test_demo_mode_returns_zero(parser):
    code = _run(parser, ["--path", "secret/app", "--demo"])
    assert code == 0


def test_no_demo_without_real_client_returns_one(parser):
    code = _run(parser, ["--path", "secret/app"])
    assert code == 1


def test_invalid_max_calls_returns_one(parser):
    code = _run(parser, ["--path", "secret/app", "--demo", "--max-calls", "0"])
    assert code == 1


def test_invalid_period_returns_one(parser):
    code = _run(parser, ["--path", "secret/app", "--demo", "--period", "0"])
    assert code == 1


def test_invalid_failure_threshold_returns_one(parser):
    code = _run(parser, ["--path", "secret/app", "--demo", "--failure-threshold", "0"])
    assert code == 1


def test_invalid_max_duration_returns_one(parser):
    code = _run(parser, ["--path", "secret/app", "--demo", "--max-duration", "0"])
    assert code == 1


def test_demo_output_contains_path(parser, capsys):
    _run(parser, ["--path", "secret/myapp", "--demo"])
    out = capsys.readouterr().out
    assert "secret/myapp" in out


def test_demo_output_is_valid_json(parser, capsys):
    import json
    _run(parser, ["--path", "secret/myapp", "--demo"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, dict)
