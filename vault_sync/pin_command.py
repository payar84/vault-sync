"""CLI subcommand for managing pinned secrets."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vault_sync.pin import PinStore

_DEFAULT_STORE = ".vault_pins.json"


def _store_from_args(args: argparse.Namespace) -> PinStore:
    return PinStore(Path(args.store))


def run_pin_command(args: argparse.Namespace) -> int:
    action = args.pin_action
    store = _store_from_args(args)

    if action == "add":
        entry = store.pin(key=args.key, path=args.path, value=args.value)
        store.save()
        print(f"Pinned {entry.key} (path={entry.path}) → {entry.hash[:12]}…")
        return 0

    if action == "remove":
        removed = store.remove(args.key)
        if removed:
            store.save()
            print(f"Removed pin for {args.key}")
            return 0
        print(f"No pin found for {args.key}", file=sys.stderr)
        return 1

    if action == "check":
        result = store.check(args.key, args.value)
        if result is None:
            print(f"{args.key} is not pinned")
            return 0
        if result:
            print(f"{args.key} matches pinned hash ✓")
            return 0
        print(f"{args.key} does NOT match pinned hash ✗", file=sys.stderr)
        return 2

    if action == "list":
        pins = store.all_pins()
        if not pins:
            print("No pins registered.")
            return 0
        for key, p in sorted(pins.items()):
            print(f"{key:30s}  path={p.path}  hash={p.hash[:12]}…  pinned_at={p.pinned_at}")
        return 0

    print(f"Unknown action: {action}", file=sys.stderr)
    return 1


def _configure_parser(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--store", default=_DEFAULT_STORE, help="Path to pin store JSON")
    actions = sub.add_subparsers(dest="pin_action", required=True)

    add_p = actions.add_parser("add", help="Pin a secret value")
    add_p.add_argument("key", help="Secret key name")
    add_p.add_argument("path", help="Vault path")
    add_p.add_argument("value", help="Secret value to hash and pin")

    rem_p = actions.add_parser("remove", help="Remove a pin")
    rem_p.add_argument("key", help="Secret key name")

    chk_p = actions.add_parser("check", help="Check value against pin")
    chk_p.add_argument("key", help="Secret key name")
    chk_p.add_argument("value", help="Current value to verify")

    actions.add_parser("list", help="List all pinned secrets")


def add_pin_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("pin", help="Manage pinned secret values")
    _configure_parser(p)
    p.set_defaults(func=run_pin_command)


def build_pin_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync pin")
    _configure_parser(parser)
    return parser
