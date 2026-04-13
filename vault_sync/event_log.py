"""Event log for tracking vault-sync lifecycle events."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional


class EventType(str, Enum):
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    SECRET_READ = "secret_read"
    SECRET_WRITE = "secret_write"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"


@dataclass
class Event:
    event_type: EventType
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class EventLog:
    _events: List[Event] = field(default_factory=list)

    def record(self, event_type: EventType, message: str, **metadata) -> Event:
        event = Event(event_type=event_type, message=message, metadata=metadata)
        self._events.append(event)
        return event

    def all_events(self) -> List[Event]:
        return list(self._events)

    def filter_by_type(self, event_type: EventType) -> List[Event]:
        return [e for e in self._events if e.event_type == event_type]

    def write(self, path: Path) -> None:
        entries = [e.to_dict() for e in self._events]
        path.write_text(json.dumps(entries, indent=2))

    def load(self, path: Path) -> None:
        if not path.exists():
            return
        raw = json.loads(path.read_text())
        for entry in raw:
            evt = Event(
                event_type=EventType(entry["event_type"]),
                message=entry["message"],
                timestamp=entry["timestamp"],
                metadata=entry.get("metadata", {}),
            )
            self._events.append(evt)

    def clear(self) -> None:
        self._events.clear()
