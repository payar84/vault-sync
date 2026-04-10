"""Local cache for Vault secrets to reduce redundant reads."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


DEFAULT_TTL = 300  # seconds
DEFAULT_CACHE_PATH = Path(".vault_cache.json")


@dataclass
class CacheEntry:
    value: str
    fetched_at: float
    ttl: int = DEFAULT_TTL

    def is_expired(self) -> bool:
        return (time.time() - self.fetched_at) > self.ttl

    def to_dict(self) -> dict:
        return {"value": self.value, "fetched_at": self.fetched_at, "ttl": self.ttl}

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        return cls(
            value=data["value"],
            fetched_at=data["fetched_at"],
            ttl=data.get("ttl", DEFAULT_TTL),
        )


@dataclass
class SecretCache:
    ttl: int = DEFAULT_TTL
    cache_path: Path = field(default_factory=lambda: DEFAULT_CACHE_PATH)
    _store: Dict[str, CacheEntry] = field(default_factory=dict, init=False, repr=False)

    def load(self) -> None:
        """Load cache from disk if it exists."""
        if not self.cache_path.exists():
            return
        try:
            raw = json.loads(self.cache_path.read_text())
            self._store = {
                k: CacheEntry.from_dict(v) for k, v in raw.items()
            }
        except (json.JSONDecodeError, KeyError):
            self._store = {}

    def save(self) -> None:
        """Persist cache to disk."""
        self.cache_path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._store.items()}, indent=2)
        )

    def get(self, key: str) -> Optional[str]:
        """Return cached value if present and not expired."""
        entry = self._store.get(key)
        if entry is None or entry.is_expired():
            return None
        return entry.value

    def set(self, key: str, value: str) -> None:
        """Store a value in the cache."""
        self._store[key] = CacheEntry(value=value, fetched_at=time.time(), ttl=self.ttl)

    def invalidate(self, key: str) -> None:
        """Remove a single key from the cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
