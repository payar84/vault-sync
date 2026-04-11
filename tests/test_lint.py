"""Tests for vault_sync.lint and vault_sync.lint_command."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from vault_sync.lint import LintIssue, LintResult, lint_env_file
from vault_sync.lint_command import run_lint_command


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> None:
    path.write_text(content)


# --- LintIssue / LintResult ---

def test_lint_issue_repr():
    issue = LintIssue(key="FOO", message="bad", severity="error")
    assert repr(issue) == "[ERROR] FOO: bad"


def test_lint_result_ok_when_no_errors(env_file):
    result = LintResult(path=env_file)
    result.issues.append(LintIssue(key="X", message="warn", severity="warning"))
    assert result.ok is True


def test_lint_result_not_ok_when_errors(env_file):
    result = LintResult(path=env_file)
    result.issues.append(LintIssue(key="X", message="err", severity="error"))
    assert result.ok is False


def test_lint_result_counts(env_file):
    result = LintResult(path=env_file)
    result.issues.append(LintIssue(key="A", message="e", severity="error"))
    result.issues.append(LintIssue(key="B", message="w", severity="warning"))
    assert result.error_count == 1
    assert result.warning_count == 1


# --- lint_env_file ---

def test_missing_file_returns_error(env_file):
    result = lint_env_file(env_file)
    assert result.error_count == 1
    assert not result.ok


def test_clean_file_has_no_issues(env_file):
    _write(env_file, "API_KEY=abc123\nDB_HOST=localhost\n")
    result = lint_env_file(env_file)
    assert result.issues == []
    assert result.ok


def test_empty_value_produces_warning(env_file):
    _write(env_file, "API_KEY=\n")
    result = lint_env_file(env_file)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("empty" in i.message.lower() for i in warnings)


def test_invalid_key_produces_error(env_file):
    _write(env_file, "bad-key=value\n")
    result = lint_env_file(env_file)
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("invalid" in e.message.lower() for e in errors)


def test_lowercase_key_produces_error(env_file):
    _write(env_file, "my_key=value\n")
    result = lint_env_file(env_file)
    assert any(i.severity == "error" for i in result.issues)


# --- run_lint_command ---

def _make_args(env_file: Path, strict: bool = False, quiet: bool = False) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, strict=strict, quiet=quiet)


def test_command_exits_zero_for_clean_file(env_file):
    _write(env_file, "GOOD_KEY=value\n")
    assert run_lint_command(_make_args(env_file)) == 0


def test_command_exits_one_for_error(env_file):
    _write(env_file, "bad-key=value\n")
    assert run_lint_command(_make_args(env_file)) == 1


def test_strict_mode_exits_one_for_warnings(env_file):
    _write(env_file, "EMPTY_VAL=\n")
    assert run_lint_command(_make_args(env_file, strict=True)) == 1


def test_non_strict_mode_exits_zero_for_warnings(env_file):
    _write(env_file, "EMPTY_VAL=\n")
    assert run_lint_command(_make_args(env_file, strict=False)) == 0


def test_quiet_mode_suppresses_output(env_file, capsys):
    _write(env_file, "GOOD_KEY=value\n")
    run_lint_command(_make_args(env_file, quiet=True))
    captured = capsys.readouterr()
    assert captured.out == ""
