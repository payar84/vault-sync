"""Event dispatcher for routing sync lifecycle events to registered handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


EventHandler = Callable[[str, dict], None]


@dataclass
class Dispatcher:
    """Routes named events to registered handler functions."""

    _handlers: Dict[str, List[EventHandler]] = field(default_factory=dict)

    def on(self, event: str, handler: EventHandler) -> None:
        """Register a handler for the given event name."""
        self._handlers.setdefault(event, []).append(handler)

    def off(self, event: str, handler: EventHandler) -> bool:
        """Unregister a handler. Returns True if it was found and removed."""
        handlers = self._handlers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False

    def emit(self, event: str, payload: dict | None = None) -> int:
        """Emit an event, calling all registered handlers. Returns handler count."""
        payload = payload or {}
        handlers = self._handlers.get(event, [])
        for handler in list(handlers):
            handler(event, payload)
        return len(handlers)

    def events(self) -> List[str]:
        """Return list of event names that have at least one handler."""
        return [e for e, h in self._handlers.items() if h]

    def handler_count(self, event: str) -> int:
        """Return the number of handlers registered for the given event."""
        return len(self._handlers.get(event, []))

    def clear(self, event: str | None = None) -> None:
        """Remove all handlers for a specific event, or all events if None."""
        if event is None:
            self._handlers.clear()
        else:
            self._handlers.pop(event, None)


def make_dispatcher() -> Dispatcher:
    """Factory returning a fresh Dispatcher instance."""
    return Dispatcher()
