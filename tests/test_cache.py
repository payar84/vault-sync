"""Tests for vault_sync.cache module."""

import json
import time
from pathlib import Path

import pytest

from vault_sync.cache import CacheEntry, SecretCache, DEFAULT_TTL


@pytest.fixture
def cache_file(tmp_path: Path) -> Path:
    return tmp_path / ".vault_cache.json"


@pytest.fixture
def cache(cache_file: Path) -> SecretCache:
    return SecretCache(ttl=60, cache_path=cache_file)


def test_get_returns_none_when_empty(cache: SecretCache) -> None:
    assert cache.get("MY_KEY") is None


def test_set_and_get_value(cache: SecretCache) -> None:
    cache.set("DB_PASSWORD", "secret123")
    assert cache.get("DB_PASSWORD") == "secret123"


def test_expired_entry_returns_none(cache: SecretCache) -> None:
    entry = CacheEntry(value="old_value", fetched_at=time.time() - 120, ttl=60)
    cache._store["STALE_KEY"] = entry
    assert cache.get("STALE_KEY") is None


def test_non_expired_entry_is_returned(cache: SecretCache) -> None:
    entry = CacheEntry(value="fresh", fetched_at=time.time() - 10, ttl=60)
    cache._store["FRESH_KEY"] = entry
    assert cache.get("FRESH_KEY") == "fresh"


def test_invalidate_removes_key(cache: SecretCache) -> None:
    cache.set("TOKEN", "abc")
    cache.invalidate("TOKEN")
    assert cache.get("TOKEN") is None


def test_invalidate_missing_key_is_safe(cache: SecretCache) -> None:
    cache.invalidate("NONEXISTENT")  # should not raise


def test_clear_removes_all(cache: SecretCache) -> None:
    cache.set("A", "1")
    cache.set("B", "2")
    cache.clear()
    assert len(cache) == 0


def test_save_and_load_roundtrip(cache: SecretCache, cache_file: Path) -> None:
    cache.set("API_KEY", "xyz")
    cache.save()
    assert cache_file.exists()

    new_cache = SecretCache(ttl=60, cache_path=cache_file)
    new_cache.load()
    assert new_cache.get("API_KEY") == "xyz"


def test_load_handles_missing_file(cache_file: Path) -> None:
    c = SecretCache(cache_path=cache_file)
    c.load()  # should not raise
    assert len(c) == 0


def test_load_handles_corrupt_file(cache_file: Path) -> None:
    cache_file.write_text("not valid json{{")
    c = SecretCache(cache_path=cache_file)
    c.load()  # should not raise
    assert len(c) == 0


def test_cache_entry_is_expired_flag() -> None:
    old = CacheEntry(value="v", fetched_at=time.time() - 400, ttl=DEFAULT_TTL)
    assert old.is_expired()

    fresh = CacheEntry(value="v", fetched_at=time.time(), ttl=DEFAULT_TTL)
    assert not fresh.is_expired()


def test_to_dict_and_from_dict_roundtrip() -> None:
    entry = CacheEntry(value="hello", fetched_at=1700000000.0, ttl=120)
    restored = CacheEntry.from_dict(entry.to_dict())
    assert restored.value == entry.value
    assert restored.fetched_at == entry.fetched_at
    assert restored.ttl == entry.ttl
