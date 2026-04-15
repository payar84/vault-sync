"""CLI subcommand for inspecting the sync ledger."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vault_sync.ledger import Ledger


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ledger-file", default=".vault_ledger.json", help="Path to ledger file")
    sub = parser.add_subparsers(dest="ledger_action")

    sub.add_parser("list", help="List all ledger entries")

    rm = sub.add_parser("remove", help="Remove a key from the ledger")
    rm.add_argument("key", help="Key to remove")

    show = sub.add_parser("show", help="Show details for a single key")
    show.add_argument("key", help="Key to show")


def run_ledger_command(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger_file)
    ledger = Ledger.load(ledger_path)
    action = getattr(args, "ledger_action", None)

    if action == "list" or action is None:
        entries = ledger.all_entries()
        if not entries:
            print("Ledger is empty.")
            return 0
        for e in entries:
            checksum_part = f"  checksum={e.checksum[:8]}" if e.checksum else ""
            print(f"{e.key}  path={e.path}  env={e.env_file}  synced_at={e.synced_at}{checksum_part}")
        return 0

    if action == "remove":
        if ledger.remove(args.key):
            ledger.save(ledger_path)
            print(f"Removed '{args.key}' from ledger.")
            return 0
        print(f"Key '{args.key}' not found in ledger.", file=sys.stderr)
        return 1

    if action == "show":
        entry = ledger.get(args.key)
        if entry is None:
            print(f"Key '{args.key}' not found in ledger.", file=sys.stderr)
            return 1
        for k, v in entry.to_dict().items():
            print(f"{k}: {v}")
        return 0

    print("No action specified. Use list, remove, or show.", file=sys.stderr)
    return 1


def add_ledger_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("ledger", help="Inspect the sync ledger")
    _configure_parser(parser)
    parser.set_defaults(func=run_ledger_command)


def build_ledger_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the vault-sync ledger")
    _configure_parser(parser)
    return parser
