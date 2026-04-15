from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SamplerConfig:
    rate: float = 1.0          # fraction of keys to sample, 0 < rate <= 1.0
    max_keys: Optional[int] = None  # hard cap on returned keys
    seed: Optional[int] = None      # for reproducible sampling

    def validate(self) -> None:
        if not (0.0 < self.rate <= 1.0):
            raise ValueError("rate must be in (0.0, 1.0]")
        if self.max_keys is not None and self.max_keys < 1:
            raise ValueError("max_keys must be a positive integer")


@dataclass
class SampleResult:
    sampled: Dict[str, str]
    total_input: int
    skipped: int

    @property
    def total_sampled(self) -> int:
        return len(self.sampled)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SampleResult(sampled={self.total_sampled}, "
            f"total_input={self.total_input}, skipped={self.skipped})"
        )


def sample_secrets(
    secrets: Dict[str, str],
    config: SamplerConfig,
) -> SampleResult:
    """Return a random subset of *secrets* according to *config*."""
    config.validate()

    keys: List[str] = sorted(secrets.keys())
    rng = random.Random(config.seed)

    if config.rate < 1.0:
        keys = [k for k in keys if rng.random() < config.rate]

    if config.max_keys is not None:
        keys = keys[: config.max_keys]

    sampled = {k: secrets[k] for k in keys}
    skipped = len(secrets) - len(sampled)
    return SampleResult(sampled=sampled, total_input=len(secrets), skipped=skipped)
