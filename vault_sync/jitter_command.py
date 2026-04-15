"""CLI sub-command: vault-sync jitter — demonstrate jitter strategies."""
from __future__ import annotations

import argparse
from typing import List

from vault_sync.jitter import JitterConfig, JitterStrategy, apply_jitter


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in JitterStrategy],
        default=JitterStrategy.FULL.value,
        help="Jitter strategy to apply (default: full)",
    )
    parser.add_argument(
        "--base-delay",
        type=float,
        default=1.0,
        dest="base_delay",
        help="Base delay in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=0.0,
        dest="min_delay",
        help="Minimum allowed delay (default: 0.0)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=30.0,
        dest="max_delay",
        help="Maximum allowed delay (default: 30.0)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of sample values to generate (default: 5)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )


def run_jitter_command(args: argparse.Namespace) -> int:
    try:
        config = JitterConfig(
            strategy=JitterStrategy(args.strategy),
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            seed=args.seed,
        )
    except ValueError as exc:
        print(f"[jitter] invalid config: {exc}")
        return 1

    print(f"Strategy : {config.strategy.value}")
    print(f"Base delay: {args.base_delay:.3f}s")
    print(f"Range     : [{config.min_delay:.3f}s, {config.max_delay:.3f}s]")
    print()

    results: List[float] = []
    for i in range(1, args.iterations + 1):
        result = apply_jitter(args.base_delay, config)
        results.append(result.jittered_delay)
        print(f"  [{i:02d}] {result}")

    avg = sum(results) / len(results) if results else 0.0
    print(f"\nAverage jittered delay: {avg:.3f}s")
    return 0


def add_jitter_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("jitter", help="Demonstrate jitter delay strategies")
    _configure_parser(parser)
    parser.set_defaults(func=run_jitter_command)


def build_jitter_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync jitter")
    _configure_parser(parser)
    return parser
