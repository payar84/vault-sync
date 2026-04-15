"""Multiplexer: fan-out secret reads across multiple Vault paths and merge results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class MultiplexConfig:
    paths: List[str]
    stop_on_error: bool = False
    deduplicate: bool = True

    def validate(self) -> None:
        if not self.paths:
            raise ValueError("paths must contain at least one entry")
        for p in self.paths:
            if not isinstance(p, str) or not p.strip():
                raise ValueError(f"invalid path entry: {p!r}")


@dataclass
class MultiplexResult:
    secrets: Dict[str, str] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    paths_read: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_keys(self) -> int:
        return len(self.secrets)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MultiplexResult(paths={len(self.paths_read)}, "
            f"keys={self.total_keys}, errors={len(self.errors)})"
        )


Fetcher = Callable[[str], Optional[Dict[str, str]]]


def multiplex(
    config: MultiplexConfig,
    fetcher: Fetcher,
) -> MultiplexResult:
    """Fan-out reads across all configured paths and merge secrets."""
    config.validate()
    result = MultiplexResult()

    for path in config.paths:
        try:
            data = fetcher(path)
        except Exception as exc:  # noqa: BLE001
            result.errors[path] = str(exc)
            if config.stop_on_error:
                break
            continue

        if data is None:
            result.errors[path] = "path returned no data"
            if config.stop_on_error:
                break
            continue

        result.paths_read.append(path)
        for key, value in data.items():
            if config.deduplicate and key in result.secrets:
                continue
            result.secrets[key] = value

    return result
