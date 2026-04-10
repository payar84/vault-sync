"""Template rendering for .env files using secret values from Vault."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")


@dataclass
class RenderResult:
    rendered: str
    resolved: list[str]
    missing: list[str]

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0

    def __repr__(self) -> str:
        return (
            f"RenderResult(resolved={len(self.resolved)}, "
            f"missing={len(self.missing)}, ok={self.ok})"
        )


def render_template(template: str, secrets: Dict[str, str]) -> RenderResult:
    """Replace {{ KEY }} placeholders with values from secrets dict."""
    resolved: list[str] = []
    missing: list[str] = []

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in secrets:
            resolved.append(key)
            return secrets[key]
        missing.append(key)
        return match.group(0)

    rendered = _PLACEHOLDER_RE.sub(replacer, template)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_resolved = [k for k in resolved if not (k in seen or seen.add(k))]  # type: ignore[func-returns-value]
    unique_missing = list(dict.fromkeys(missing))
    return RenderResult(rendered=rendered, resolved=unique_resolved, missing=unique_missing)


def render_template_file(
    template_path: Path,
    secrets: Dict[str, str],
    output_path: Optional[Path] = None,
) -> RenderResult:
    """Read a template file, render it, and optionally write the result."""
    template = template_path.read_text(encoding="utf-8")
    result = render_template(template, secrets)
    if output_path is not None:
        output_path.write_text(result.rendered, encoding="utf-8")
    return result


def collect_placeholders(template: str) -> list[str]:
    """Return a deduplicated list of placeholder keys found in the template."""
    return list(dict.fromkeys(m.group(1) for m in _PLACEHOLDER_RE.finditer(template)))
