"""CLI sub-command: finalizer demo."""
from __future__ import annotations

import argparse
from typing import List, Optional

from vault_sync.finalizer import Finalizer, FinalizerConfig


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        default=False,
        help="Halt callback chain on first error",
    )
    parser.add_argument(
        "--max-callbacks",
        type=int,
        default=32,
        metavar="N",
        help="Maximum number of registered callbacks (default: 32)",
    )
    parser.add_argument(
        "action",
        choices=["demo", "status"],
        nargs="?",
        default="demo",
        help="Action to perform",
    )


def run_finalizer_command(args: argparse.Namespace) -> int:
    try:
        cfg = FinalizerConfig(
            stop_on_error=args.stop_on_error,
            max_callbacks=args.max_callbacks,
        )
        cfg.validate()
    (f"[finalizer] config error: {exc}")
        return 1

    finalizer = Finalizer(cfg)

    if args.action == "status":
        print(f"[finalizer] registered={finalizer.count} cap={cfg.max_callbacks}")
        return 0

    # demo: register a couple of sample callbacks
    finalizer.register(lambda: print("[finalizer] callback 1: cleanup temp files"))
    finalizer.register(lambda: print("[finalizer] callback 2: flush audit log"))

    result = finalizer.run()
    print(f"[finalizer] ran={result.ran} errors={len(result.errors)} ok={result.ok}")
    return 0 if result.ok else 1


def add_finalizer_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("finalizer", help="Run post-sync cleanup callbacks")
    _configure_parser(parser)
    parser.set_defaults(func=run_finalizer_command)


def build_finalizer_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync finalizer")
    _configure_parser(parser)
    return parser
