"""CLI subcommand for demonstrating deadline enforcement."""
from __future__ import annotations

import argparse
import time

from vault_sync.deadline import make_deadline


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=5.0,
        help="Maximum allowed duration in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--warn-at",
        type=float,
        default=0.8,
        help="Fraction of max_seconds at which to warn (default: 0.8)",
    )
    parser.add_argument(
        "--simulate-seconds",
        type=float,
        default=0.0,
        help="Seconds to simulate elapsed time before checking status",
    )


def run_deadline_command(args: argparse.Namespace) -> int:
    try:
        dl = make_deadline(args.max_seconds, args.warn_at)
    except ValueError as exc:
        print(f"[deadline] config error: {exc}")
        return 1

    if args.simulate_seconds > 0:
        time.sleep(min(args.simulate_seconds, 2.0))  # cap sleep in CLI demo

    status = dl.status()
    print(repr(status))
    print(f"  remaining : {status.remaining:.3f}s")

    if status.expired:
        print("[deadline] EXPIRED — operation would be aborted")
        return 2
    if status.warned:
        print("[deadline] WARNING — approaching deadline")
    else:
        print("[deadline] OK")
    return 0


def add_deadline_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("deadline", help="Check or simulate deadline enforcement")
    _configure_parser(parser)
    parser.set_defaults(func=run_deadline_command)


def build_deadline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync deadline")
    _configure_parser(parser)
    return parser
