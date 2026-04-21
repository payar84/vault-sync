"""Observer pattern implementation for vault-sync secret change notifications.

Provides a lightweight pub/sub mechanism that allows components to subscribe
to specific secret lifecycle events without tight coupling.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class ObserverEvent(str, Enum):
    SECRET_READ = "secret_read"
    SECRET_WRITTEN = "secret_written"
    SECRET_DELETED = "secret_deleted"
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"


@dataclass
class ObserverNotification:
    """Payload delivered to observer callbacks."""

    event: ObserverEvent
    path: str
    metadata: Dict[str, object] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, object]:
        return {
            "event": self.event.value,
            "path": self.path,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


# Callback type: receives a notification, returns nothing.
ObserverCallback = Callable[[ObserverNotification], None]


@dataclass
class ObserverConfig:
    """Configuration for the observer registry."""

    max_subscribers_per_event: int = 32

    def validate(self) -> None:
        if self.max_subscribers_per_event < 1:
            raise ValueError("max_subscribers_per_event must be >= 1")


class Observer:
    """Registry that manages event subscriptions and fan-out delivery."""

    def __init__(self, config: Optional[ObserverConfig] = None) -> None:
        self._config = config or ObserverConfig()
        self._config.validate()
        self._subscribers: Dict[ObserverEvent, List[ObserverCallback]] = {
            e: [] for e in ObserverEvent
        }

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    def subscribe(self, event: ObserverEvent, callback: ObserverCallback) -> None:
        """Register *callback* to be called whenever *event* is emitted."""
        bucket = self._subscribers[event]
        if len(bucket) >= self._config.max_subscribers_per_event:
            raise RuntimeError(
                f"Subscriber limit ({self._config.max_subscribers_per_event}) "
                f"reached for event '{event.value}'"
            )
        if callback not in bucket:
            bucket.append(callback)

    def unsubscribe(self, event: ObserverEvent, callback: ObserverCallback) -> bool:
        """Remove *callback* from *event*. Returns True if it was present."""
        bucket = self._subscribers[event]
        try:
            bucket.remove(callback)
            return True
        except ValueError:
            return False

    def subscriber_count(self, event: ObserverEvent) -> int:
        """Return the number of subscribers registered for *event*."""
        return len(self._subscribers[event])

    # ------------------------------------------------------------------
    # Notification delivery
    # ------------------------------------------------------------------

    def notify(
        self,
        event: ObserverEvent,
        path: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> int:
        """Emit *event* for *path*, invoking all registered callbacks.

        Returns the number of callbacks that were invoked.
        """
        notification = ObserverNotification(
            event=event,
            path=path,
            metadata=metadata or {},
        )
        callbacks = list(self._subscribers[event])
        for cb in callbacks:
            cb(notification)
        return len(callbacks)

    def clear(self, event: Optional[ObserverEvent] = None) -> None:
        """Remove all subscribers, optionally scoped to a single *event*."""
        if event is not None:
            self._subscribers[event].clear()
        else:
            for bucket in self._subscribers.values():
                bucket.clear()
