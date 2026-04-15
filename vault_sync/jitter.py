"""Jitter strategies for randomising retry/backoff delays."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class JitterStrategy(str, Enum):
    NONE = "none"
    FULL = "full"
    EQUAL = "equal"
    DECORRELATED = "decorrelated"


@dataclass
class JitterConfig:
    strategy: JitterStrategy = JitterStrategy.FULL
    min_delay: float = 0.0
    max_delay: float = 30.0
    seed: Optional[int] = None
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.validate()
        self._rng = random.Random(self.seed)

    def validate(self) -> None:
        if self.min_delay < 0:
            raise ValueError("min_delay must be >= 0")
        if self.max_delay <= 0:
            raise ValueError("max_delay must be > 0")
        if self.min_delay >= self.max_delay:
            raise ValueError("min_delay must be less than max_delay")


@dataclass
class JitterResult:
    base_delay: float
    jittered_delay: float
    strategy: JitterStrategy

    def __repr__(self) -> str:
        return (
            f"JitterResult(strategy={self.strategy.value}, "
            f"base={self.base_delay:.3f}s, jittered={self.jittered_delay:.3f}s)"
        )


def apply_jitter(base_delay: float, config: JitterConfig) -> JitterResult:
    """Apply the configured jitter strategy to *base_delay* and return a JitterResult."""
    rng = config._rng
    lo = config.min_delay
    hi = config.max_delay

    if config.strategy == JitterStrategy.NONE:
        jittered = base_delay
    elif config.strategy == JitterStrategy.FULL:
        jittered = rng.uniform(lo, min(base_delay, hi))
    elif config.strategy == JitterStrategy.EQUAL:
        half = base_delay / 2.0
        jittered = half + rng.uniform(0, min(half, hi - lo))
    elif config.strategy == JitterStrategy.DECORRELATED:
        prev = base_delay
        jittered = min(hi, rng.uniform(lo, prev * 3))
    else:
        jittered = base_delay

    jittered = max(lo, min(jittered, hi))
    return JitterResult(base_delay=base_delay, jittered_delay=jittered, strategy=config.strategy)
