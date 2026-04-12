"""Tokenizer: split secret paths into structured tokens for indexing and search."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TokenizedPath:
    raw: str
    segments: List[str] = field(default_factory=list)
    tokens: Dict[str, str] = field(default_factory=dict)

    def depth(self) -> int:
        return len(self.segments)

    def leaf(self) -> Optional[str]:
        return self.segments[-1] if self.segments else None

    def parent(self) -> Optional[str]:
        if len(self.segments) < 2:
            return None
        return "/".join(self.segments[:-1])

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "segments": self.segments,
            "tokens": self.tokens,
            "depth": self.depth(),
            "leaf": self.leaf(),
            "parent": self.parent(),
        }


def tokenize_path(path: str) -> TokenizedPath:
    """Split a vault secret path into segments and extract named tokens."""
    clean = path.strip("/")
    segments = [s for s in clean.split("/") if s]
    tokens: Dict[str, str] = {}
    for i, seg in enumerate(segments):
        tokens[f"seg{i}"] = seg
    if segments:
        tokens["leaf"] = segments[-1]
    if len(segments) >= 2:
        tokens["parent"] = segments[-2]
    if len(segments) >= 3:
        tokens["root"] = segments[0]
    return TokenizedPath(raw=path, segments=segments, tokens=tokens)


def filter_by_token(paths: List[str], token_key: str, token_value: str) -> List[str]:
    """Return paths whose token at *token_key* matches *token_value* (case-insensitive)."""
    needle = token_value.lower()
    result = []
    for p in paths:
        tp = tokenize_path(p)
        if tp.tokens.get(token_key, "").lower() == needle:
            result.append(p)
    return result


def group_by_parent(paths: List[str]) -> Dict[str, List[str]]:
    """Group paths by their parent segment."""
    groups: Dict[str, List[str]] = {}
    for p in paths:
        tp = tokenize_path(p)
        key = tp.parent() or ""
        groups.setdefault(key, []).append(p)
    return groups
