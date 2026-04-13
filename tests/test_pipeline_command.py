"""Tests for vault_sync.pipeline_command."""
from __future__ import annotations

import json
import pytest

from vault_sync.pipeline_command import build_pipeline_parser, run_pipeline_command


@pytest.fixture()
def parser():
    return build_pipeline_parser()


def _run(args_list):
    p = build_pipeline_parser()
    args = p.parse_args(args_list)
    return run_pipeline_command(args)


_BASE = json.dumps({"DB_PASSWORD": "secret", "API_KEY": "abc", "APP_DEBUG": "true"})


def test_basic_run_returns_zero():
    assert _run(["--secrets", _BASE]) == 0


def test_invalid_secrets_json_returns_one():
    assert _run(["--secrets", "not-json"]) == 1


def test_invalid_aliases_json_returns_one():
    assert _run(["--secrets", _BASE, "--aliases", "bad"]) == 1


def test_exclude_filter_applied(capsys):
    _run(["--secrets", _BASE, "--exclude", "debug"])
    out = capsys.readouterr().out
    assert "APP_DEBUG" not in out or "dropped" in out


def test_transform_strip_applied(capsys):
    secrets = json.dumps({"KEY": "  value  "})
    _run(["--secrets", secrets, "--transform", "strip"])
    out = capsys.readouterr().out
    assert "value" in out


def test_alias_rename_applied(capsys):
    secrets = json.dumps({"old_key": "val"})
    aliases = json.dumps({"old_key": "NEW_KEY"})
    _run(["--secrets", secrets, "--aliases", aliases])
    out = capsys.readouterr().out
    assert "NEW_KEY" in out


def test_result_repr_printed(capsys):
    _run(["--secrets", _BASE])
    out = capsys.readouterr().out
    assert "PipelineResult" in out
