"""Merge strategies for combining Vault secrets with existing .env values."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class MergeStrategy(str, Enum):
    VAULT_WINS = "vault_wins"      # Vault always overwrites local
    LOCAL_WINS = "local_wins"      # Keep local values if present
    PROMPT = "prompt"              # Not handled here; caller must resolve
    NEW_ONLY = "new_only"          # Only add keys absent from local


@dataclass
class MergeResult:
    merged: Dict[str, str]
    overwritten: int = 0
    preserved: int = 0
    added: int = 0

    @property
    def total(self) -> int:
        return self.overwritten + self.preserved + self.added

    def __repr__(self) -> str:
        return (
            f"MergeResult(added={self.added}, overwritten={self.overwritten}, "
            f"preserved={self.preserved})"
        )


def merge_secrets(
    vault_secrets: Dict[str, str],
    local_secrets: Dict[str, str],
    strategy: MergeStrategy = MergeStrategy.VAULT_WINS,
) -> MergeResult:
    """Merge vault_secrets into local_secrets using the given strategy."""
    merged: Dict[str, str] = dict(local_secrets)
    overwritten = 0
    preserved = 0
    added = 0

    for key, vault_value in vault_secrets.items():
        if key not in local_secrets:
            merged[key] = vault_value
            added += 1
        elif strategy == MergeStrategy.VAULT_WINS:
            if merged[key] != vault_value:
                merged[key] = vault_value
                overwritten += 1
            else:
                preserved += 1
        elif strategy == MergeStrategy.LOCAL_WINS:
            preserved += 1
        elif strategy == MergeStrategy.NEW_ONLY:
            preserved += 1
        else:
            # PROMPT falls through; caller is responsible
            preserved += 1

    return MergeResult(
        merged=merged,
        overwritten=overwritten,
        preserved=preserved,
        added=added,
    )


def parse_strategy(value: Optional[str]) -> MergeStrategy:
    """Parse a string into a MergeStrategy, raising ValueError on unknown values."""
    if value is None:
        return MergeStrategy.VAULT_WINS
    try:
        return MergeStrategy(value.lower())
    except ValueError:
        valid = ", ".join(s.value for s in MergeStrategy)
        raise ValueError(f"Unknown merge strategy '{value}'. Valid options: {valid}")
