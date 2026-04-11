"""CLI subcommand: vault-sync lint — check a .env file for issues."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vault_sync.lint import lint_env_file


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "env_file",
        type=Path,
        help="Path to the .env file to lint",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warnings as errors (exit non-zero if any warnings exist)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output; only use exit code to signal result",
    )


def run_lint_command(args: argparse.Namespace) -> int:
    result = lint_env_file(args.env_file)

    if not args.quiet:
        if not result.issues:
            print(f"✔  No issues found in {args.env_file}")
        else:
            for issue in sorted(result.issues, key=lambda i: (i.severity, i.key)):
                print(repr(issue))
            print(
                f"\n{args.env_file}: "
                f"{result.error_count} error(s), {result.warning_count} warning(s)"
            )

    if not result.ok:
        return 1
    if args.strict and result.warning_count > 0:
        return 1
    return 0


def add_lint_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "lint",
        help="Check a .env file for common issues",
    )
    _configure_parser(parser)
    parser.set_defaults(func=run_lint_command)


def build_lint_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vault-sync lint",
        description="Lint a .env file for duplicate keys, empty values, and naming issues.",
    )
    _configure_parser(parser)
    return parser


if __name__ == "__main__":  # pragma: no cover
    _parser = build_lint_parser()
    _args = _parser.parse_args()
    sys.exit(run_lint_command(_args))
