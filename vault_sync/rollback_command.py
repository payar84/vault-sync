from __future__ import annotations

import argparse
from pathlib import Path

from vault_sync.backup import list_backups
from vault_sync.rollback import rollback_to_latest, rollback_to_timestamp


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env-file", required=True, help="Path to the .env file to restore")
    parser.add_argument("--backup-dir", default=".vault_backups", help="Directory containing backups")
    sub = parser.add_subparsers(dest="rollback_action")

    sub.add_parser("latest", help="Restore the most recent backup")

    ts_p = sub.add_parser("to", help="Restore a backup matching a timestamp prefix")
    ts_p.add_argument("timestamp", help="ISO timestamp prefix to match (e.g. 2024-01)")

    sub.add_parser("list", help="List available backups")


def run_rollback_command(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    backup_dir = Path(args.backup_dir)
    action = getattr(args, "rollback_action", None) or "latest"

    if action == "list":
        backups = list_backups(backup_dir, env_path)
        if not backups:
            print("No backups found.")
        for b in backups:
            print(f"  {b.timestamp}  {b.backup_path}")
        return 0

    if action == "to":
        result = rollback_to_timestamp(env_path, backup_dir, args.timestamp)
    else:
        result = rollback_to_latest(env_path, backup_dir)

    print(result.message)
    return 0 if result.success else 1


def add_rollback_subcommand(subparsers) -> None:
    p = subparsers.add_parser("rollback", help="Roll back a .env file to a previous backup")
    _configure_parser(p)
    p.set_defaults(func=run_rollback_command)


def build_rollback_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync rollback")
    _configure_parser(parser)
    return parser
