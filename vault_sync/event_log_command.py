"""CLI subcommand for inspecting the vault-sync event log."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from vault_sync.event_log import EventLog, EventType


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--log-file", default=".vault_events.json", help="Path to event log file")
    sub = parser.add_subparsers(dest="event_action")

    show = sub.add_parser("show", help="Print all recorded events")
    show.add_argument("--type", dest="event_type", default=None, help="Filter by event type")
    show.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")

    sub.add_parser("clear", help="Clear the event log")
    sub.add_parser("types", help="List available event types")


def run_event_log_command(args: argparse.Namespace) -> int:
    log_path = Path(args.log_file)
    log = EventLog()
    log.load(log_path)

    action = getattr(args, "event_action", None) or "show"

    if action == "types":
        for et in EventType:
            print(et.value)
        return 0

    if action == "clear":
        log.clear()
        log.write(log_path)
        print("Event log cleared.")
        return 0

    # show
    events = log.all_events()
    if getattr(args, "event_type", None):
        try:
            et = EventType(args.event_type)
        except ValueError:
            print(f"Unknown event type: {args.event_type}")
            return 1
        events = [e for e in events if e.event_type == et]

    if not events:
        print("No events found.")
        return 0

    if getattr(args, "as_json", False):
        print(json.dumps([e.to_dict() for e in events], indent=2))
    else:
        for e in events:
            print(f"[{e.timestamp}] {e.event_type.value}: {e.message}")
            if e.metadata:
                for k, v in e.metadata.items():
                    print(f"  {k}: {v}")
    return 0


def add_event_log_subcommand(subparsers) -> None:
    parser = subparsers.add_parser("event-log", help="Inspect the vault-sync event log")
    _configure_parser(parser)
    parser.set_defaults(func=run_event_log_command)


def build_event_log_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Event log inspector")
    _configure_parser(parser)
    return parser
