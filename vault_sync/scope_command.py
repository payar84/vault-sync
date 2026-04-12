"""CLI subcommand: vault-sync scope — preview which paths are in scope."""
from __future__ import annotations

import argparse
import sys
from typing import List

from vault_sync.scope import parse_scope


_SAMPLE_PATHS = [
    "secret/app/prod/db",
    "secret/app/prod/api",
    "secret/app/staging/db",
    "secret/infra/network",
    "secret/infra/tls",
    "secret/shared/oauth",
]


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--include",
        nargs="*",
        metavar="PATTERN",
        default=[],
        help="Glob patterns for paths to include (default: all)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        metavar="PATTERN",
        default=[],
        help="Glob patterns for paths to exclude",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        metavar="PATH",
        default=None,
        help="Paths to evaluate (default: built-in sample set)",
    )


def run_scope_command(args: argparse.Namespace) -> int:
    scope = parse_scope(include=args.include, exclude=args.exclude)
    paths: List[str] = args.paths if args.paths is not None else _SAMPLE_PATHS

    in_scope = scope.filter_paths(paths)
    out_of_scope = [p for p in paths if p not in in_scope]

    print(f"In scope  ({len(in_scope)}):")
    for p in sorted(in_scope):
        print(f"  + {p}")

    if out_of_scope:
        print(f"\nExcluded  ({len(out_of_scope)}):")
        for p in sorted(out_of_scope):
            print(f"  - {p}")

    return 0


def add_scope_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "scope",
        help="Preview which Vault paths are in scope for a sync",
    )
    _configure_parser(parser)
    parser.set_defaults(func=run_scope_command)


def build_scope_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync scope")
    _configure_parser(parser)
    return parser
