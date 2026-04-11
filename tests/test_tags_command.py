"""Tests for vault_sync.tags_command."""
import json
import pytest

from vault_sync.tags_command import build_tags_parser, run_tags_command


@pytest.fixture()
def parser():
    return build_tags_parser()


# ---------------------------------------------------------------------------
# filter action
# ---------------------------------------------------------------------------

def test_filter_action_returns_zero(parser, capsys):
    args = parser.parse_args(["filter", "--match", "env=prod"])
    args.tags_action = "filter"
    rc = run_tags_command(args)
    assert rc == 0


def test_filter_prints_matching_paths(parser, capsys):
    args = parser.parse_args(["filter", "--match", "env=prod,team=backend"])
    args.tags_action = "filter"
    run_tags_command(args)
    out = capsys.readouterr().out
    assert "secret/app/db" in out
    assert "secret/app/cache" in out
    assert "secret/app/email" not in out


def test_filter_no_match_prints_message(parser, capsys):
    args = parser.parse_args(["filter", "--match", "env=dev"])
    args.tags_action = "filter"
    run_tags_command(args)
    out = capsys.readouterr().out
    assert "No secrets matched" in out


def test_filter_invalid_tag_returns_one(parser, capsys):
    args = parser.parse_args(["filter", "--match", "badformat"])
    args.tags_action = "filter"
    rc = run_tags_command(args)
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error" in err


# ---------------------------------------------------------------------------
# group action
# ---------------------------------------------------------------------------

def test_group_action_returns_zero(parser, capsys):
    args = parser.parse_args(["group", "--key", "env"])
    args.tags_action = "group"
    rc = run_tags_command(args)
    assert rc == 0


def test_group_output_is_valid_json(parser, capsys):
    args = parser.parse_args(["group", "--key", "env"])
    args.tags_action = "group"
    run_tags_command(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, dict)


def test_group_output_contains_env_keys(parser, capsys):
    args = parser.parse_args(["group", "--key", "env"])
    args.tags_action = "group"
    run_tags_command(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "prod" in data
    assert "staging" in data


def test_unknown_action_returns_one(capsys):
    class FakeArgs:
        tags_action = "unknown"
    rc = run_tags_command(FakeArgs())
    assert rc == 1
