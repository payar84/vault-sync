import argparse
import pytest
from unittest.mock import patch, MagicMock

from vault_sync.notify_command import run_notify_command, build_notify_parser
from vault_sync.notify import NotifyResult


@pytest.fixture
def parser():
    return build_notify_parser()


def _run(args_list):
    p = build_notify_parser()
    args = p.parse_args(args_list)
    return run_notify_command(args)


def test_successful_run_returns_zero():
    ok_result = NotifyResult.ok(stdout="done")
    with patch("vault_sync.notify_command.run_notify", return_value=ok_result):
        assert _run(["echo", "hello"]) == 0


def test_failed_run_returns_one():
    fail_result = NotifyResult(success=False, returncode=1, stdout="", stderr="err")
    with patch("vault_sync.notify_command.run_notify", return_value=fail_result):
        assert _run(["false"]) == 1


def test_invalid_config_returns_one():
    # empty command triggers validation error
    p = build_notify_parser()
    args = p.parse_args([""])
    result = run_notify_command(args)
    assert result == 1


def test_invalid_env_entry_returns_one():
    ok_result = NotifyResult.ok()
    with patch("vault_sync.notify_command.run_notify", return_value=ok_result):
        p = build_notify_parser()
        args = p.parse_args(["echo", "--env", "BADENTRY"])
        assert run_notify_command(args) == 1


def test_env_vars_are_parsed_and_passed():
    ok_result = NotifyResult.ok()
    with patch("vault_sync.notify_command.run_notify", return_value=ok_result) as mock_run:
        p = build_notify_parser()
        args = p.parse_args(["echo", "--env", "FOO=bar", "BAZ=qux"])
        run_notify_command(args)
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["env_vars"] == {"FOO": "bar", "BAZ": "qux"}


def test_timeout_is_forwarded():
    ok_result = NotifyResult.ok()
    with patch("vault_sync.notify_command.run_notify", return_value=ok_result) as mock_run:
        p = build_notify_parser()
        args = p.parse_args(["echo", "--timeout", "15"])
        run_notify_command(args)
        config_arg = mock_run.call_args.args[0]
        assert config_arg.timeout == 15


def test_error_message_is_printed_on_failure(capsys):
    fail_result = NotifyResult(
        success=False, returncode=1, stdout="", stderr="", error="command not found: xyz"
    )
    with patch("vault_sync.notify_command.run_notify", return_value=fail_result):
        _run(["xyz"])
        captured = capsys.readouterr()
        assert "command not found" in captured.err
