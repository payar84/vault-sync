"""Orchestrates syncing secrets from Vault to a local .env file."""

from typing import Optional
import logging

from vault_sync.client import VaultClient
from vault_sync.config import VaultConfig
from vault_sync.env_writer import read_env_file, write_env_file
from vault_sync.namespace import Namespace, apply_namespace

logger = logging.getLogger(__name__)


class SyncResult:
    """Holds statistics from a sync operation."""

    def __init__(self):
        self.added: list[str] = []
        self.updated: list[str] = []
        self.unchanged: list[str] = []
        self.errors: list[str] = []

    @property
    def total(self) -> int:
        return len(self.added) + len(self.updated) + len(self.unchanged)

    def __repr__(self) -> str:
        return (
            f"SyncResult(added={len(self.added)}, updated={len(self.updated)}, "
            f"unchanged={len(self.unchanged)}, errors={len(self.errors)})"
        )


def sync_secrets(
    client: VaultClient,
    namespaces: list[Namespace],
    env_path: str,
    dry_run: bool = False,
) -> SyncResult:
    """Fetch secrets for all namespaces and write them to an .env file."""
    result = SyncResult()
    existing = read_env_file(env_path)
    merged: dict[str, str] = dict(existing)

    for ns in namespaces:
        logger.debug("Fetching secrets from path: %s", ns.path)
        try:
            raw_secrets = client.read_secret(ns.path)
        except Exception as exc:
            logger.error("Failed to read '%s': %s", ns.path, exc)
            result.errors.append(ns.path)
            continue

        transformed = apply_namespace(raw_secrets, ns)

        for key, value in transformed.items():
            if key not in existing:
                result.added.append(key)
            elif existing[key] != value:
                result.updated.append(key)
            else:
                result.unchanged.append(key)
            merged[key] = value

    if not dry_run:
        write_env_file(env_path, merged)
        logger.info("Written %d keys to %s", len(merged), env_path)
    else:
        logger.info("[dry-run] Would write %d keys to %s", len(merged), env_path)

    return result
