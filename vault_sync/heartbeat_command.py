from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from vault_sync.heartbeat import Heartbeat, HeartbeatConfig


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--label", default="default", help="Heartbeat label")
    parser.add_argument("--interval", type=float, default=30.0, help="Interval in seconds")
    parser.add_argument("--max-misses", type=int, default=3, help="Max allowed misses")
    sub = parser.add_subparsers(dest="hb_action")
    sub.add_parser("beat", help="Record a heartbeat")
    sub.add_parser("miss", help="Record a missed beat")
    sub.add_parser("status", help="Show current status")
    sub.add_parser("reset", help="Reset heartbeat state")


def run_heartbeat_command(args: argparse.Namespace) -> int:
    try:
        cfg = HeartbeatConfig(
            interval_seconds=args.interval,
            max_misses=args.max_misses,
            label=args.label,
        )
        cfg.validate()
    except ValueError as exc:
        print(f"[heartbeat] config error: {exc}", file=sys.stderr)
        return 1

    hb = Heartbeat(config=cfg)
    action = getattr(args, "hb_action", None) or "status"

    if action == "beat":
        hb.beat()
        print(f"[heartbeat] beat recorded for '{cfg.label}'")
    elif action == "miss":
        hb.miss()
        status = hb.status()
        print(f"[heartbeat] miss recorded — miss_count={status.miss_count}")
    elif action == "reset":
        hb.reset()
        print(f"[heartbeat] reset for '{cfg.label}'")
    else:
        status = hb.status()
        print(repr(status))

    return 0


def add_heartbeat_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("heartbeat", help="Manage heartbeat monitoring")
    _configure_parser(parser)
    parser.set_defaults(func=run_heartbeat_command)


def build_heartbeat_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync heartbeat")
    _configure_parser(parser)
    return parser
