"""Secret reference resolution — expands {{path:key}} placeholders using Vault secrets."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

_REF_RE = re.compile(r"\{\{([^}:]+):([^}]+)\}\}")


@dataclass
class ResolveResult:
    value: str
    resolved: List[Tuple[str, str]] = field(default_factory=list)  # (path, key) pairs
    unresolved: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.unresolved) == 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ResolveResult(ok={self.ok}, resolved={len(self.resolved)}, "
            f"unresolved={len(self.unresolved)})"
        )


def resolve_references(
    value: str,
    fetch: Callable[[str, str], Optional[str]],
) -> ResolveResult:
    """Replace all {{path:key}} references in *value* using *fetch(path, key)*.

    *fetch* should return the secret string or ``None`` if unavailable.
    Unresolvable references are left verbatim in the output.
    """
    resolved: List[Tuple[str, str]] = []
    unresolved: List[Tuple[str, str]] = []

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        path, key = m.group(1).strip(), m.group(2).strip()
        secret = fetch(path, key)
        if secret is None:
            unresolved.append((path, key))
            return m.group(0)  # leave placeholder intact
        resolved.append((path, key))
        return secret

    result = _REF_RE.sub(_replace, value)
    return ResolveResult(value=result, resolved=resolved, unresolved=unresolved)


def resolve_dict(
    secrets: Dict[str, str],
    fetch: Callable[[str, str], Optional[str]],
) -> Tuple[Dict[str, str], List[Tuple[str, str, str]]]:
    """Resolve references across an entire secrets dict.

    Returns the updated dict and a list of (key, path, ref_key) triples for
    every reference that could *not* be resolved.
    """
    out: Dict[str, str] = {}
    all_unresolved: List[Tuple[str, str, str]] = []
    for k, v in secrets.items():
        res = resolve_references(v, fetch)
        out[k] = res.value
        for path, ref_key in res.unresolved:
            all_unresolved.append((k, path, ref_key))
    return out, all_unresolved
