"""Fluent builder for PipelineConfig."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from vault_sync.pipeline import PipelineConfig
from vault_sync.filter import FilterConfig
from vault_sync.alias import AliasMap


class PipelineBuilder:
    """Construct a PipelineConfig step by step.

    Example::

        config = (
            PipelineBuilder()
            .include("db_", "app_")
            .exclude("debug")
            .transform(strip_whitespace)
            .alias({"db_password": "DATABASE_PASSWORD"})
            .build()
        )
    """

    def __init__(self) -> None:
        self._include: List[str] = []
        self._exclude: List[str] = []
        self._transforms: List[Callable[[str, str], str]] = []
        self._aliases: Dict[str, str] = {}

    def include(self, *prefixes: str) -> "PipelineBuilder":
        self._include.extend(prefixes)
        return self

    def exclude(self, *patterns: str) -> "PipelineBuilder":
        self._exclude.extend(patterns)
        return self

    def transform(self, fn: Callable[[str, str], str]) -> "PipelineBuilder":
        self._transforms.append(fn)
        return self

    def alias(self, mapping: Dict[str, str]) -> "PipelineBuilder":
        self._aliases.update(mapping)
        return self

    def build(self) -> PipelineConfig:
        filter_cfg: Optional[FilterConfig] = None
        if self._include or self._exclude:
            filter_cfg = FilterConfig(
                include_prefixes=list(self._include),
                exclude_patterns=list(self._exclude),
            )

        alias_map: Optional[AliasMap] = None
        if self._aliases:
            alias_map = AliasMap(aliases=dict(self._aliases))

        return PipelineConfig(
            filter_config=filter_cfg,
            transforms=list(self._transforms),
            alias_map=alias_map,
        )

    def reset(self) -> "PipelineBuilder":
        """Clear all accumulated configuration and return self."""
        self._include = []
        self._exclude = []
        self._transforms = []
        self._aliases = {}
        return self
