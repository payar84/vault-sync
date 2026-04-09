"""CLI entry point for vault-sync."""

import argparse
import json
import logging
import sys

from vault_sync.config import VaultConfig, from_env
from vault_sync.client import VaultClient
from vault_sync.namespace import parse_namespaces
from vault_sync.syncer import sync_secrets

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vault-sync",
        description="Sync secrets from HashiCorp Vault to a local .env file.",
    )
    parser.add_argument(
        "--namespaces",
        required=True,
        help="JSON string or path to JSON file defining namespace mappings.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to the target .env file (default: .env).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to disk.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def load_namespaces_arg(value: str) -> list[dict]:
    """Accept inline JSON string or a path to a JSON file."""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        with open(value) as fh:
            return json.load(fh)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config: VaultConfig = from_env()
    client = VaultClient(config)

    if not client.is_authenticated():
        logger.error("Vault authentication failed. Check VAULT_ADDR and VAULT_TOKEN.")
        sys.exit(1)

    raw_ns = load_namespaces_arg(args.namespaces)
    namespaces = parse_namespaces(raw_ns)

    result = sync_secrets(client, namespaces, args.env_file, dry_run=args.dry_run)

    print(f"Sync complete: {result}")
    if result.errors:
        sys.exit(2)


if __name__ == "__main__":
    main()
