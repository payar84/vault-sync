"""CLI subcommand for inspecting dispatcher event registrations."""

from __future__ import annotations

import argparse
import json
from typing import List

from vault_sync.dispatcher import Dispatcher, make_dispatcher


def _build_sample_dispatcher() -> Dispatcher:
    """Return a dispatcher pre-populated with example handlers for demo purposes."""
    d = make_dispatcher()

    def _noop(event: str, payload: dict) -> None:  # pragma: no cover
        pass

    d.on("sync.start", _noop)
    d.on("sync.complete", _noop)
    d.on("sync.complete", _noop)
    d.on("auth.failure", _noop)
    return d


def run_dispatcher_command(args: argparse.Namespace) -> int:
    dispatcher = _build_sample_dispatcher()

    if args.action == "list":
        events = dispatcher.events()
        if not events:
            print("No events registered.")
            return 0
        for event in sorted(events):
            count = dispatcher.handler_count(event)
            print(f"{event}: {count} handler(s)")
        return 0

    if args.action == "show":
        event = args.event
        count = dispatcher.handler_count(event)
        result = {"event": event, "handler_count": count}
        print(json.dumps(result, indent=2))
        return 0

    print(f"Unknown action: {args.action}")
    return 1


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list", help="List all registered event names")
    show = sub.add_parser("show", help="Show handler count for a specific event")
    show.add_argument("event", help="Event name to inspect")


def add_dispatcher_subcommand(subparsers) -> None:
    p = subparsers.add_parser("dispatcher", help="Inspect event dispatcher registrations")
    _configure_parser(p)
    p.set_defaults(func=run_dispatcher_command)


def build_dispatcher_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync dispatcher")
    _configure_parser(parser)
    return parser
