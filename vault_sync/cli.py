"""CLI entry point for vault-sync."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from vault_sync.config import VaultConfig
from vault_sync.namespace import parse_namespaces
from vault_sync.watcher import WatchConfig, run_watcher

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vault-sync",
        description="Sync secrets from HashiCorp Vault to .env files.",
    )
    parser.add_argument("--env-file", default=".env", help="Target .env file path")
    parser.add_argument("--namespaces", help="JSON file or inline JSON array of namespace configs")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    sub = parser.add_subparsers(dest="command")

    # watch sub-command
    watch_p = sub.add_parser("watch", help="Poll Vault and re-sync on interval")
    watch_p.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Polling interval in seconds (default: 30)",
    )
    watch_p.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Stop after N iterations (omit for infinite loop)",
    )

    return parser


def load_namespaces_arg(value: str | None):
    if value is None:
        return []
    path = Path(value)
    if path.exists():
        raw = json.loads(path.read_text())
    else:
        raw = json.loads(value)
    return parse_namespaces(raw)


def _build_sync_fn(args: argparse.Namespace):
    """Return a zero-argument callable that performs one sync cycle."""
    from vault_sync.client import VaultClient
    from vault_sync.syncer import sync_secrets

    def _sync() -> None:
        config = VaultConfig.from_env()
        config.validate()
        client = VaultClient(config)
        namespaces = load_namespaces_arg(args.namespaces)
        sync_secrets(
            client=client,
            namespaces=namespaces,
            env_file=args.env_file,
            dry_run=args.dry_run,
        )

    return _sync


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.command == "watch":
        watch_cfg = WatchConfig(
            interval_seconds=args.interval,
            max_iterations=args.max_iterations,
        )
        sync_fn = _build_sync_fn(args)
        result = run_watcher(watch_cfg, sync_fn)
        logger.info("Watch finished: %s", result)
        return 0 if result.error_count == 0 else 1

    # default: single sync
    try:
        _build_sync_fn(args)()
    except Exception as exc:  # noqa: BLE001
        logger.error("Sync failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
