from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class QuotaConfig:
    max_keys: Optional[int] = None
    max_paths: Optional[int] = None
    warn_at: float = 0.8  # fraction of limit that triggers a warning

    def validate(self) -> None:
        if self.max_keys is not None and self.max_keys <= 0:
            raise ValueError("max_keys must be a positive integer")
        if self.max_paths is not None and self.max_paths <= 0:
            raise ValueError("max_paths must be a positive integer")
        if not (0.0 < self.warn_at <= 1.0):
            raise ValueError("warn_at must be between 0 (exclusive) and 1 (inclusive)")


@dataclass
class QuotaStatus:
    key_count: int
    path_count: int
    config: QuotaConfig
    warnings: list = field(default_factory=list)
    exceeded: bool = False

    def __post_init__(self) -> None:
        self._evaluate()

    def _evaluate(self) -> None:
        if self.config.max_keys is not None:
            ratio = self.key_count / self.config.max_keys
            if self.key_count > self.config.max_keys:
                self.exceeded = True
                self.warnings.append(
                    f"Key quota exceeded: {self.key_count}/{self.config.max_keys}"
                )
            elif ratio >= self.config.warn_at:
                self.warnings.append(
                    f"Key quota warning: {self.key_count}/{self.config.max_keys} "
                    f"({ratio:.0%})"
                )

        if self.config.max_paths is not None:
            ratio = self.path_count / self.config.max_paths
            if self.path_count > self.config.max_paths:
                self.exceeded = True
                self.warnings.append(
                    f"Path quota exceeded: {self.path_count}/{self.config.max_paths}"
                )
            elif ratio >= self.config.warn_at:
                self.warnings.append(
                    f"Path quota warning: {self.path_count}/{self.config.max_paths} "
                    f"({ratio:.0%})"
                )

    def ok(self) -> bool:
        return not self.exceeded

    def __repr__(self) -> str:
        state = "OK" if self.ok() else "EXCEEDED"
        return (
            f"QuotaStatus({state}, keys={self.key_count}, paths={self.path_count})"
        )


def check_quota(
    secrets: Dict[str, Dict[str, str]],
    config: QuotaConfig,
) -> QuotaStatus:
    """Evaluate quota usage given a mapping of path -> {key: value}."""
    path_count = len(secrets)
    key_count = sum(len(v) for v in secrets.values())
    return QuotaStatus(
        key_count=key_count,
        path_count=path_count,
        config=config,
    )
