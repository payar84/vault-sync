"""CLI subcommand for secret rotation status reporting."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Dict, Optional

from vault_sync.rotation import RotationPolicy, RotationTracker


def _load_records(path: str) -> Dict[str, str]:
    """Load rotation records from a JSON file."""
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def _save_records(path: str, records: Dict[str, str]) -> None:
    with open(path, "w") as fh:
        json.dump(records, fh, indent=2)


def run_rotation_command(args: argparse.Namespace) -> int:
    policy = RotationPolicy(
        max_age_days=args.max_age_days,
        warn_before_days=args.warn_before_days,
    )
    policy.validate()
    tracker = RotationTracker(policy=policy)

    records = _load_records(args.records_file)
    for key, ts in records.items():
        tracker.record_rotation(key, datetime.fromisoformat(ts))

    if args.rotation_action == "mark":
        for key in args.keys:
            tracker.record_rotation(key)
        updated = {k: v.isoformat() for k, v in tracker._records.items()}
        _save_records(args.records_file, updated)
        print(f"Marked {len(args.keys)} key(s) as rotated.")
        return 0

    keys = args.keys or list(records.keys())
    statuses = tracker.check_all(keys)
    for s in statuses:
        print(repr(s))

    expired = [s for s in statuses if s.is_expired]
    if expired and args.fail_on_expired:
        print(f"ERROR: {len(expired)} expired secret(s) found.")
        return 1
    return 0


def _configure_parser(p: argparse.ArgumentParser) -> None:
    p.add_argument("--records-file", default=".rotation_records.json")
    p.add_argument("--max-age-days", type=int, default=90)
    p.add_argument("--warn-before-days", type=int, default=14)
    p.add_argument("--fail-on-expired", action="store_true")
    p.add_argument("keys", nargs="*", help="Secret keys to check or mark")
    sub = p.add_subparsers(dest="rotation_action")
    sub.add_parser("mark", help="Mark keys as rotated now")
    sub.add_parser("check", help="Check rotation status")


def add_rotation_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("rotation", help="Check or mark secret rotation status")
    _configure_parser(p)
    p.set_defaults(func=run_rotation_command)


def build_rotation_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vault-sync rotation")
    _configure_parser(p)
    return p
