"""Pruner: remove stale keys from .env files that no longer exist in Vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class PruneResult:
    removed: List[str] = field(default_factory=list)
    kept: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed)

    @property
    def total_kept(self) -> int:
        return len(self.kept)

    @property
    def ok(self) -> bool:
        return True

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PruneResult(removed={self.total_removed}, kept={self.total_kept})"
        )


def compute_stale_keys(
    local: Dict[str, str],
    vault: Dict[str, str],
) -> Set[str]:
    """Return keys present in *local* but absent from *vault*."""
    return set(local.keys()) - set(vault.keys())


def prune_secrets(
    local: Dict[str, str],
    vault: Dict[str, str],
    *,
    dry_run: bool = False,
) -> PruneResult:
    """Remove stale keys from *local* that are no longer in *vault*.

    When *dry_run* is True the returned result reflects what *would* be
    removed but the ``local`` dict is left unchanged.
    """
    stale = compute_stale_keys(local, vault)
    result = PruneResult(
        removed=sorted(stale),
        kept=sorted(set(local.keys()) - stale),
    )

    if not dry_run:
        for key in stale:
            del local[key]

    return result
