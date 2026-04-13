"""Tests for vault_sync.dispatcher."""

from __future__ import annotations

import pytest

from vault_sync.dispatcher import Dispatcher, make_dispatcher


@pytest.fixture()
def dispatcher() -> Dispatcher:
    return make_dispatcher()


def test_emit_calls_registered_handler(dispatcher: Dispatcher) -> None:
    received: list = []
    dispatcher.on("sync.start", lambda e, p: received.append((e, p)))
    dispatcher.emit("sync.start", {"key": "value"})
    assert received == [("sync.start", {"key": "value"})]


def test_emit_returns_handler_count(dispatcher: Dispatcher) -> None:
    dispatcher.on("sync.start", lambda e, p: None)
    dispatcher.on("sync.start", lambda e, p: None)
    count = dispatcher.emit("sync.start")
    assert count == 2


def test_emit_unknown_event_returns_zero(dispatcher: Dispatcher) -> None:
    assert dispatcher.emit("no.such.event") == 0


def test_emit_with_no_payload_uses_empty_dict(dispatcher: Dispatcher) -> None:
    received: list = []
    dispatcher.on("test", lambda e, p: received.append(p))
    dispatcher.emit("test")
    assert received == [{}]


def test_multiple_handlers_all_called(dispatcher: Dispatcher) -> None:
    calls: list = []
    dispatcher.on("ev", lambda e, p: calls.append(1))
    dispatcher.on("ev", lambda e, p: calls.append(2))
    dispatcher.emit("ev")
    assert calls == [1, 2]


def test_off_removes_handler(dispatcher: Dispatcher) -> None:
    calls: list = []
    handler = lambda e, p: calls.append(1)  # noqa: E731
    dispatcher.on("ev", handler)
    removed = dispatcher.off("ev", handler)
    assert removed is True
    dispatcher.emit("ev")
    assert calls == []


def test_off_returns_false_when_not_registered(dispatcher: Dispatcher) -> None:
    assert dispatcher.off("ev", lambda e, p: None) is False


def test_events_lists_registered_event_names(dispatcher: Dispatcher) -> None:
    dispatcher.on("a", lambda e, p: None)
    dispatcher.on("b", lambda e, p: None)
    assert set(dispatcher.events()) == {"a", "b"}


def test_events_excludes_cleared_event(dispatcher: Dispatcher) -> None:
    dispatcher.on("a", lambda e, p: None)
    dispatcher.clear("a")
    assert "a" not in dispatcher.events()


def test_clear_all_removes_all_events(dispatcher: Dispatcher) -> None:
    dispatcher.on("a", lambda e, p: None)
    dispatcher.on("b", lambda e, p: None)
    dispatcher.clear()
    assert dispatcher.events() == []


def test_handler_count_returns_correct_number(dispatcher: Dispatcher) -> None:
    dispatcher.on("ev", lambda e, p: None)
    dispatcher.on("ev", lambda e, p: None)
    assert dispatcher.handler_count("ev") == 2


def test_handler_count_zero_for_unknown_event(dispatcher: Dispatcher) -> None:
    assert dispatcher.handler_count("unknown") == 0


def test_make_dispatcher_returns_fresh_instance() -> None:
    d1 = make_dispatcher()
    d2 = make_dispatcher()
    d1.on("ev", lambda e, p: None)
    assert d2.handler_count("ev") == 0
