"""CLI subcommand: vault-sync circuit-breaker — inspect/reset circuit-breaker state."""
from __future__ import annotations

import argparse
import json
from typing import List

from vault_sync.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState

# Module-level singleton so other commands can share one breaker instance.
_default_breaker = CircuitBreaker(
    config=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30.0,
        success_threshold=2,
    )
)


def get_default_breaker() -> CircuitBreaker:
    return _default_breaker


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="cb_action", required=True)
    sub.add_parser("status", help="Print current circuit-breaker state")
    sub.add_parser("reset", help="Reset circuit breaker to CLOSED state")
    check = sub.add_parser("check", help="Exit non-zero if circuit is OPEN")
    check.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output status as JSON",
    )


def run_circuit_breaker_command(
    args: argparse.Namespace,
    breaker: CircuitBreaker | None = None,
) -> int:
    cb = breaker or _default_breaker

    if args.cb_action == "reset":
        cb.reset()
        print("Circuit breaker reset to CLOSED.")
        return 0

    state = cb.state
    if args.cb_action == "status":
        print(repr(cb))
        return 0

    # check
    payload = {
        "state": state.value,
        "failures": cb._failure_count,
        "open": state == CircuitState.OPEN,
    }
    if getattr(args, "as_json", False):
        print(json.dumps(payload))
    else:
        print(f"state={payload['state']}  failures={payload['failures']}")

    return 1 if state == CircuitState.OPEN else 0


def add_circuit_breaker_subcommand(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
) -> None:
    parser = subparsers.add_parser(
        "circuit-breaker",
        help="Inspect or reset the Vault client circuit breaker",
    )
    _configure_parser(parser)
    parser.set_defaults(func=run_circuit_breaker_command)


def build_circuit_breaker_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vault-sync circuit-breaker",
        description="Manage the Vault client circuit breaker",
    )
    _configure_parser(parser)
    return parser
