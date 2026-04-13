"""Trace secret resolution paths for debugging and auditing."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class TraceEntry:
    key: str
    path: str
    resolved: bool
    value_preview: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "path": self.path,
            "resolved": self.resolved,
            "value_preview": self.value_preview,
            "timestamp": self.timestamp,
            "note": self.note,
        }

    def __repr__(self) -> str:  # pragma: no cover
        status = "OK" if self.resolved else "MISS"
        return f"TraceEntry({status} {self.key!r} @ {self.path!r})"


@dataclass
class Tracer:
    _entries: List[TraceEntry] = field(default_factory=list)

    def record(
        self,
        key: str,
        path: str,
        value: Optional[str],
        note: Optional[str] = None,
    ) -> TraceEntry:
        preview = _preview(value)
        entry = TraceEntry(
            key=key,
            path=path,
            resolved=value is not None,
            value_preview=preview,
            note=note,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> List[TraceEntry]:
        return list(self._entries)

    def resolved(self) -> List[TraceEntry]:
        return [e for e in self._entries if e.resolved]

    def unresolved(self) -> List[TraceEntry]:
        return [e for e in self._entries if not e.resolved]

    def summary(self) -> Dict:
        return {
            "total": len(self._entries),
            "resolved": len(self.resolved()),
            "unresolved": len(self.unresolved()),
        }

    def clear(self) -> None:
        self._entries.clear()


def _preview(value: Optional[str], max_len: int = 6) -> str:
    if value is None:
        return "<none>"
    if len(value) <= max_len:
        return "*" * len(value)
    return "*" * max_len + "..."
