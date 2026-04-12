"""CLI sub-command: tokenize — inspect and filter vault secret paths."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from vault_sync.tokenizer import filter_by_token, group_by_parent, tokenize_path

_SAMPLE_PATHS: List[str] = [
    "secret/prod/db/password",
    "secret/prod/db/username",
    "secret/prod/api/key",
    "secret/staging/db/password",
    "secret/staging/api/key",
]


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="tokenizer_action", required=True)

    inspect = sub.add_parser("inspect", help="Show token breakdown for a path")
    inspect.add_argument("path", help="Vault secret path to inspect")

    flt = sub.add_parser("filter", help="Filter sample paths by token")
    flt.add_argument("token_key", help="Token key (e.g. leaf, parent, seg0)")
    flt.add_argument("token_value", help="Expected token value")

    sub.add_parser("group", help="Group sample paths by parent segment")


def run_tokenizer_command(args: argparse.Namespace) -> int:
    action = args.tokenizer_action

    if action == "inspect":
        tp = tokenize_path(args.path)
        print(json.dumps(tp.to_dict(), indent=2))
        return 0

    if action == "filter":
        matched = filter_by_token(_SAMPLE_PATHS, args.token_key, args.token_value)
        if not matched:
            print("No paths matched.", file=sys.stderr)
            return 1
        for p in matched:
            print(p)
        return 0

    if action == "group":
        groups = group_by_parent(_SAMPLE_PATHS)
        print(json.dumps(groups, indent=2))
        return 0

    print(f"Unknown action: {action}", file=sys.stderr)
    return 1


def add_tokenizer_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "tokenize", help="Inspect and filter vault secret paths by token"
    )
    _configure_parser(parser)
    parser.set_defaults(func=run_tokenizer_command)


def build_tokenizer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vault-sync tokenize",
        description="Tokenize and filter vault secret paths.",
    )
    _configure_parser(parser)
    return parser
