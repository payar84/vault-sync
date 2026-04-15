"""CLI subcommand for inspecting cooldown state."""
from __future__ import annotations

import argparse
import time

from vault_sync.cooldown import Cooldown, CooldownConfig


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="cooldown_action", required=True)

    check = sub.add_parser("check", help="Check if a path is ready to sync")
    check.add_argument("path", help="Vault path to check")
    check.add_argument("--interval", type=float, default=60.0,
                       help="Minimum interval between syncs (seconds)")

    demo = sub.add_parser("demo", help="Demonstrate cooldown with sample paths")
    demo.add_argument("--interval", type=float, default=5.0)


def run_cooldown_command(args: argparse.Namespace) -> int:
    try:
        config = CooldownConfig(min_interval_seconds=args.interval)
        config.validate()
    except ValueError as exc:
        print(f"[error] {exc}")
        return 1

    cooldown = Cooldown(config=config)

    if args.cooldown_action == "check":
        status = cooldown.check(args.path)
        print(repr(status))
        return 0 if status.ready else 2

    if args.cooldown_action == "demo":
        paths = ["secret/app/db", "secret/app/api", "secret/infra/tls"]
        now = time.monotonic()
        cooldown.record(paths[0], now=now - 3.0)
        cooldown.record(paths[1], now=now - args.interval - 1.0)
        for p in paths:
            status = cooldown.check(p, now=now)
            print(repr(status))
        return 0

    return 1


def add_cooldown_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("cooldown", help="Manage sync cooldown state")
    _configure_parser(parser)
    parser.set_defaults(func=run_cooldown_command)


def build_cooldown_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync cooldown")
    _configure_parser(parser)
    return parser
