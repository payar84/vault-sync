"""CLI sub-command: vault-sync gateway"""
from __future__ import annotations

import argparse
import json
from typing import List

from vault_sync.gateway import Gateway, GatewayConfig, GatewayResult
from vault_sync.rate_limiter import RateLimitConfig
from vault_sync.circuit_breaker import CircuitBreakerConfig
from vault_sync.deadline import DeadlineConfig


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", required=True, help="Vault secret path to read")
    parser.add_argument("--max-calls", type=int, default=10, help="Rate limit: max calls per period")
    parser.add_argument("--period", type=float, default=1.0, help="Rate limit: period in seconds")
    parser.add_argument("--burst", type=int, default=2, help="Rate limit: burst allowance")
    parser.add_argument("--failure-threshold", type=int, default=5, help="Circuit breaker failure threshold")
    parser.add_argument("--recovery-timeout", type=float, default=30.0, help="Circuit breaker recovery timeout")
    parser.add_argument("--max-duration", type=float, default=30.0, help="Deadline max duration in seconds")
    parser.add_argument("--demo", action="store_true", help="Run with a stub client")


def run_gateway_command(args: argparse.Namespace) -> int:
    try:
        rl = RateLimitConfig(max_calls=args.max_calls, period=args.period, burst=args.burst)
        rl.validate()
        cb = CircuitBreakerConfig(
            failure_threshold=args.failure_threshold,
            recovery_timeout=args.recovery_timeout,
            success_threshold=2,
        )
        cb.validate()
        dl = DeadlineConfig(max_duration=args.max_duration, warn_at=0.8)
        dl.validate()
    except ValueError as exc:
        print(f"[gateway] config error: {exc}")
        return 1

    cfg = GatewayConfig(rate_limit=rl, circuit_breaker=cb, deadline=dl)

    if args.demo:
        class _StubClient:
            def read_secret(self, path: str):
                return {"DEMO_KEY": "demo_value", "PATH": path}
        client = _StubClient()
    else:
        print("[gateway] no real client wired in demo mode; use --demo")
        return 1

    gw = Gateway(cfg, client)
    result: GatewayResult = gw.read_secret(args.path)
    if result.success:
        print(json.dumps(result.value, indent=2))
        return 0
    print(f"[gateway] failed: {result.reason}")
    return 1


def add_gateway_subcommand(subparsers) -> None:
    parser = subparsers.add_parser("gateway", help="Read a secret through the gateway")
    _configure_parser(parser)
    parser.set_defaults(func=run_gateway_command)


def build_gateway_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync gateway")
    _configure_parser(parser)
    return parser
