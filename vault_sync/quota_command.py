from __future__ import annotations

import argparse
import json
import sys
from typing import List

from vault_sync.quota import QuotaConfig, check_quota


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--max-keys",
        type=int,
        default=None,
        metavar="N",
        help="Maximum total number of secret keys allowed",
    )
    parser.add_argument(
        "--max-paths",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of secret paths allowed",
    )
    parser.add_argument(
        "--warn-at",
        type=float,
        default=0.8,
        metavar="RATIO",
        help="Fraction of limit at which to emit a warning (default: 0.8)",
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="JSON file mapping path -> {key: value} to evaluate",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output result as JSON",
    )


def run_quota_command(args: argparse.Namespace) -> int:
    try:
        config = QuotaConfig(
            max_keys=args.max_keys,
            max_paths=args.max_paths,
            warn_at=args.warn_at,
        )
        config.validate()
    except ValueError as exc:
        print(f"[quota] config error: {exc}", file=sys.stderr)
        return 2

    try:
        with open(args.input) as fh:
            secrets = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[quota] failed to read input: {exc}", file=sys.stderr)
        return 2

    status = check_quota(secrets, config)

    if args.output_json:
        out = {
            "ok": status.ok(),
            "key_count": status.key_count,
            "path_count": status.path_count,
            "warnings": status.warnings,
        }
        print(json.dumps(out, indent=2))
    else:
        print(repr(status))
        for w in status.warnings:
            print(f"  ! {w}")

    return 0 if status.ok() else 1


def add_quota_subcommand(subparsers) -> None:
    parser = subparsers.add_parser("quota", help="Check secret quota limits")
    _configure_parser(parser)
    parser.set_defaults(func=run_quota_command)


def build_quota_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check secret quota limits")
    _configure_parser(parser)
    return parser
