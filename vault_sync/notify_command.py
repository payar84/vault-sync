from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from vault_sync.notify import NotifyConfig, NotifyResult, run_notify


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("command", help="Executable to run as notification")
    parser.add_argument("args", nargs="*", help="Arguments to pass to the command")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--on-success",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run on successful sync (default: true)",
    )
    parser.add_argument(
        "--on-failure",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run on failed sync (default: true)",
    )
    parser.add_argument(
        "--env",
        nargs="*",
        metavar="KEY=VALUE",
        help="Extra environment variables to inject",
    )


def run_notify_command(args: argparse.Namespace) -> int:
    config = NotifyConfig(
        command=args.command,
        args=args.args or [],
        timeout=args.timeout,
        on_success=args.on_success,
        on_failure=args.on_failure,
    )

    env_vars: dict = {}
    for pair in args.env or []:
        if "=" not in pair:
            print(f"[notify] invalid env entry (expected KEY=VALUE): {pair}", file=sys.stderr)
            return 1
        k, v = pair.split("=", 1)
        env_vars[k] = v

    try:
        config.validate()
    except ValueError as exc:
        print(f"[notify] config error: {exc}", file=sys.stderr)
        return 1

    result = run_notify(config, env_vars=env_vars)
    if result.success:
        print(f"[notify] {result}")
        if result.stdout:
            print(result.stdout.rstrip())
    else:
        print(f"[notify] {result}", file=sys.stderr)
        if result.error:
            print(f"[notify] error: {result.error}", file=sys.stderr)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        return 1

    return 0


def add_notify_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "notify",
        help="Run a notification command after a sync operation",
    )
    _configure_parser(parser)
    parser.set_defaults(func=run_notify_command)


def build_notify_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync notify")
    _configure_parser(parser)
    return parser
