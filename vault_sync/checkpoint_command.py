"""CLI subcommand for inspecting and managing sync checkpoints."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from vault_sync.checkpoint import Checkpoint, CheckpointConfig


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", default=".vault_checkpoint.json", help="Checkpoint file path")
    parser.add_argument("--max-entries", type=int, default=100)
    parser.add_argument("--ttl", type=float, default=86400.0, help="TTL in seconds")
    sub = parser.add_subparsers(dest="action")
    sub.add_parser("list", help="List all checkpoint entries")
    mark = sub.add_parser("mark", help="Record a checkpoint entry")
    mark.add_argument("path")
    mark.add_argument("--key-count", type=int, default=0)
    mark.add_argument("--checksum", default="")
    clear = sub.add_parser("clear", help="Clear a specific path or all entries")
    clear.add_argument("--path", default=None)


def run_checkpoint_command(args: argparse.Namespace) -> int:
    try:
        cfg = CheckpointConfig(max_entries=args.max_entries, ttl_seconds=args.ttl)
        cfg.validate()
    except ValueError as exc:
        print(f"[error] invalid config: {exc}")
        return 1

    filepath = Path(args.file)
    cp = Checkpoint(config=cfg)
    cp.load(filepath)

    action = getattr(args, "action", None) or "list"

    if action == "list":
        paths = cp.all_paths()
        if not paths:
            print("No checkpoint entries found.")
            return 0
        for p in sorted(paths):
            entry = cp.get(p)
            if entry:
                ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(entry.synced_at))
                print(f"  {p}  keys={entry.key_count}  synced_at={ts}  checksum={entry.checksum[:8]}")
        return 0

    if action == "mark":
        entry = cp.record(args.path, args.key_count, args.checksum)
        cp.save(filepath)
        print(f"[ok] recorded checkpoint for '{args.path}' ({entry.key_count} keys)")
        return 0

    if action == "clear":
        if args.path:
            cp._entries.pop(args.path, None)
            print(f"[ok] cleared checkpoint for '{args.path}'")
        else:
            cp._entries.clear()
            print("[ok] cleared all checkpoints")
        cp.save(filepath)
        return 0

    print(f"[error] unknown action: {action}")
    return 1


def add_checkpoint_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("checkpoint", help="Manage sync checkpoints")
    _configure_parser(parser)
    parser.set_defaults(func=run_checkpoint_command)


def build_checkpoint_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync checkpoint")
    _configure_parser(parser)
    return parser
