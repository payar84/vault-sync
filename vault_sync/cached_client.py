"""A VaultClient wrapper that caches secret reads using SecretCache."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from vault_sync.cache import SecretCache
from vault_sync.client import VaultClient


class CachedVaultClient:
    """Wraps VaultClient and caches secret values to reduce Vault API calls."""

    def __init__(
        self,
        client: VaultClient,
        ttl: int = 300,
        cache_path: Path = Path(".vault_cache.json"),
        persist: bool = False,
    ) -> None:
        self._client = client
        self._persist = persist
        self._cache = SecretCache(ttl=ttl, cache_path=cache_path)
        if persist:
            self._cache.load()

    # ------------------------------------------------------------------
    # Delegation
    # ------------------------------------------------------------------

    def is_authenticated(self) -> bool:
        return self._client.is_authenticated()

    # ------------------------------------------------------------------
    # Cached read
    # ------------------------------------------------------------------

    def read_secret(self, path: str, key: str) -> Optional[str]:
        """Return secret value, using cache when available."""
        cache_key = f"{path}::{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        value = self._client.read_secret(path, key)
        if value is not None:
            self._cache.set(cache_key, value)
            if self._persist:
                self._cache.save()
        return value

    def read_all(self, path: str) -> Dict[str, str]:
        """Read all key/value pairs at a Vault path, caching each entry."""
        secrets = self._client.read_all(path) if hasattr(self._client, "read_all") else {}
        for key, value in secrets.items():
            cache_key = f"{path}::{key}"
            if self._cache.get(cache_key) is None:
                self._cache.set(cache_key, value)
        if self._persist:
            self._cache.save()
        return secrets

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def invalidate(self, path: str, key: str) -> None:
        """Remove a single entry from the cache."""
        self._cache.invalidate(f"{path}::{key}")

    def clear_cache(self) -> None:
        """Wipe the entire in-memory (and persisted) cache."""
        self._cache.clear()
        if self._persist and self._cache.cache_path.exists():
            self._cache.save()

    @property
    def cache(self) -> SecretCache:
        return self._cache
