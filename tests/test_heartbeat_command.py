import argparse
import pytest
from vault_sync.heartbeat_command import build_heartbeat_parser, run_heartbeat_command


@pytest.fixture
def parser():
    return build_heartbeat_parser()


def _run(parser, argv):
    args = parser.parse_args(argv)
    return run_heartbeat_command(args)


def test_status_action_returns_zero(parser):
    assert _run(parser, ["status"]) == 0


def test_beat_action_returns_zero(parser):
    assert _run(parser, ["beat"]) == 0


def test_miss_action_returns_zero(parser):
    assert _run(parser, ["miss"]) == 0


def test_reset_action_returns_zero(parser):
    assert _run(parser, ["reset"]) == 0


def test_custom_label_is_accepted(parser):
    assert _run(parser, ["--label", "my-service", "beat"]) == 0


def test_invalid_interval_returns_one(parser):
    assert _run(parser, ["--interval", "0", "status"]) == 1


def test_invalid_max_misses_returns_one(parser):
    assert _run(parser, ["--max-misses", "0", "status"]) == 1


def test_default_action_shows_status(parser, capsys):
    _run(parser, ["--label", "demo"])
    out = capsys.readouterr().out
    assert "demo" in out


def test_beat_output_mentions_label(parser, capsys):
    _run(parser, ["--label", "svc", "beat"])
    out = capsys.readouterr().out
    assert "svc" in out


def test_miss_output_shows_count(parser, capsys):
    _run(parser, ["miss"])
    out = capsys.readouterr().out
    assert "miss_count" in out
