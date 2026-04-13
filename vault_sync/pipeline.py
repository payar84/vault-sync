"""Secret pipeline: chain transforms, filters, and alias resolution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from vault_sync.filter import FilterConfig, apply_filter
from vault_sync.transform import apply_transforms
from vault_sync.alias import AliasMap


@dataclass
class PipelineConfig:
    filter_config: Optional[FilterConfig] = None
    transforms: List[Callable[[str, str], str]] = field(default_factory=list)
    alias_map: Optional[AliasMap] = None


@dataclass
class PipelineResult:
    secrets: Dict[str, str]
    dropped: List[str] = field(default_factory=list)
    renamed: Dict[str, str] = field(default_factory=dict)  # original -> final

    @property
    def total(self) -> int:
        return len(self.secrets)

    def __repr__(self) -> str:
        return (
            f"PipelineResult(total={self.total}, "
            f"dropped={len(self.dropped)}, renamed={len(self.renamed)})"
        )


def run_pipeline(
    secrets: Dict[str, str],
    config: PipelineConfig,
) -> PipelineResult:
    """Apply filter → transforms → alias resolution in order."""
    dropped: List[str] = []
    renamed: Dict[str, str] = {}

    # 1. Filter
    if config.filter_config is not None:
        filtered = apply_filter(secrets, config.filter_config)
        dropped = [k for k in secrets if k not in filtered]
        working = filtered
    else:
        working = dict(secrets)

    # 2. Transforms
    if config.transforms:
        working = apply_transforms(working, config.transforms)

    # 3. Alias resolution
    if config.alias_map is not None:
        resolved: Dict[str, str] = {}
        for key, value in working.items():
            new_key = config.alias_map.resolve(key)
            if new_key != key:
                renamed[key] = new_key
            resolved[new_key] = value
        working = resolved

    return PipelineResult(secrets=working, dropped=dropped, renamed=renamed)
