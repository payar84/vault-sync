"""CLI subcommand for watermark inspection."""
from __future__ import annotations

import argparse
from pathlib import Path

from vault_sync.watermark import Watermark, WatermarkConfig


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--store", default=".vault_watermark.json", help="Watermark store file")
    sub = parser.add_subparsers(dest="wm_action")

    show = sub.add_parser("show", help="Show latest watermark per path")
    show.add_argument("--path", default=None, help="Filter to a specific vault path")

    peak = sub.add_parser("peak", help="Show peak (max key count) per path")
    peak.add_argument("path", help="Vault path to inspect")

    sub.add_parser("paths", help="List all tracked paths")


def run_watermark_command(args: argparse.Namespace) -> int:
    store_path = Path(args.store)
    wm = Watermark(config=WatermarkConfig())
    wm.load(store_path)

    action = getattr(args, "wm_action", None) or "show"

    if action == "show":
        paths = [args.path] if getattr(args, "path", None) else wm.all_paths()
        if not paths:
            print("No watermark entries recorded.")
            return 0
        for p in paths:
            entry = wm.latest(p)
            if entry:
                print(f"{entry.path}  keys={entry.key_count}  at={entry.synced_at}")
        return 0

    if action == "peak":
        entry = wm.peak(args.path)
        if entry is None:
            print(f"No entries found for path: {args.path}")
            return 1
        print(f"{entry.path}  peak_keys={entry.key_count}  at={entry.synced_at}")
        return 0

    if action == "paths":
        paths = wm.all_paths()
        if not paths:
            print("No paths tracked.")
        else:
            for p in paths:
                print(p)
        return 0

    print(f"Unknown action: {action}")
    return 1


def add_watermark_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("watermark", help="Inspect sync watermarks")
    _configure_parser(parser)
    parser.set_defaults(func=run_watermark_command)


def build_watermark_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync watermark")
    _configure_parser(parser)
    return parser
