"""CLI sub-command: vault-sync expiry — report secret age and expiry status."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from vault_sync.expiry import ExpiryConfig, check_expiry


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--records",
        required=True,
        help="JSON file mapping vault path -> last-synced ISO timestamp",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=90,
        dest="max_age_days",
        help="Days before a secret is considered expired (default: 90)",
    )
    parser.add_argument(
        "--warn-before-days",
        type=int,
        default=14,
        dest="warn_before_days",
        help="Days before expiry to start warning (default: 14)",
    )
    parser.add_argument(
        "--fail-on-expired",
        action="store_true",
        dest="fail_on_expired",
        help="Exit with code 1 if any secrets are expired",
    )


def run_expiry_command(args: argparse.Namespace) -> int:
    records_path = Path(args.records)
    if not records_path.exists():
        print(f"[expiry] records file not found: {records_path}", file=sys.stderr)
        return 1

    try:
        records: dict = json.loads(records_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"[expiry] invalid JSON in records file: {exc}", file=sys.stderr)
        return 1

    try:
        config = ExpiryConfig(
            max_age_days=args.max_age_days,
            warn_before_days=args.warn_before_days,
        )
    except ValueError as exc:
        print(f"[expiry] invalid config: {exc}", file=sys.stderr)
        return 1

    report = check_expiry(records, config=config)

    for status in report.statuses:
        tag = "EXPIRED" if status.expired else ("WARN" if status.warning else "OK")
        print(f"  [{tag:7s}] {status.message}")

    print(f"\n{report}")

    if args.fail_on_expired and not report.ok:
        return 1
    return 0


def add_expiry_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("expiry", help="Check secret expiry status")
    _configure_parser(parser)
    parser.set_defaults(func=run_expiry_command)


def build_expiry_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="vault-sync expiry checker")
    _configure_parser(parser)
    return parser
