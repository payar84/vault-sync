"""CLI subcommand: vault-sync merge — merge Vault secrets into a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vault_sync.env_writer import read_env_file, write_env_file
from vault_sync.merge import MergeStrategy, merge_secrets, parse_strategy


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("env_file", help="Path to the target .env file")
    parser.add_argument(
        "--source",
        required=True,
        help="Path to a .env file containing incoming (Vault) secrets",
    )
    parser.add_argument(
        "--strategy",
        default=MergeStrategy.VAULT_WINS.value,
        help=(
            "Merge strategy: vault_wins (default), local_wins, new_only. "
            "'prompt' is not supported in non-interactive mode."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing anything",
    )


def run_merge_command(args: argparse.Namespace) -> int:
    try:
        strategy = parse_strategy(args.strategy)
    except ValueError as exc:
        print(f"[merge] error: {exc}", file=sys.stderr)
        return 1

    if strategy == MergeStrategy.PROMPT:
        print("[merge] error: 'prompt' strategy is not supported via CLI", file=sys.stderr)
        return 1

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"[merge] error: source file not found: {source_path}", file=sys.stderr)
        return 1

    vault_secrets = read_env_file(source_path)
    target_path = Path(args.env_file)
    local_secrets = read_env_file(target_path) if target_path.exists() else {}

    result = merge_secrets(vault_secrets, local_secrets, strategy=strategy)

    if args.dry_run:
        print(f"[merge] dry-run — strategy={strategy.value}")
        print(f"  added:       {result.added}")
        print(f"  overwritten: {result.overwritten}")
        print(f"  preserved:   {result.preserved}")
        return 0

    write_env_file(target_path, result.merged)
    print(
        f"[merge] done — added={result.added}, "
        f"overwritten={result.overwritten}, preserved={result.preserved}"
    )
    return 0


def add_merge_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("merge", help="Merge Vault secrets into a .env file")
    _configure_parser(parser)
    parser.set_defaults(func=run_merge_command)


def build_merge_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync merge")
    _configure_parser(parser)
    return parser
