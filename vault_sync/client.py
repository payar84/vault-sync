"""Vault client wrapper for fetching secrets."""

from typing import Any, Dict

import hvac

from vault_sync.config import VaultConfig


class VaultClient:
    """Thin wrapper around hvac.Client with namespace and KV v2 support."""

    def __init__(self, config: VaultConfig) -> None:
        self.config = config
        self._client = self._build_client()

    def _build_client(self) -> hvac.Client:
        kwargs: Dict[str, Any] = {
            "url": self.config.vault_addr,
            "token": self.config.vault_token,
        }
        if self.config.vault_namespace:
            kwargs["namespace"] = self.config.vault_namespace

        client = hvac.Client(**kwargs)
        return client

    def is_authenticated(self) -> bool:
        """Return True if the current token is valid."""
        try:
            return self._client.is_authenticated()
        except Exception:
            return False

    def read_secret(self, path: str) -> Dict[str, str]:
        """Read a KV v2 secret at *path* and return its data dict."""
        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.config.mount_point,
                raise_on_deleted_version=True,
            )
            return response["data"]["data"]
        except hvac.exceptions.InvalidPath as exc:
            raise KeyError(f"Secret path '{path}' not found in Vault.") from exc
        except hvac.exceptions.Forbidden as exc:
            raise PermissionError(
                f"Access denied to secret path '{path}'. Check token permissions."
            ) from exc
