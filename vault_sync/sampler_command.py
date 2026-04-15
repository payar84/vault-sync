from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from vault_sync.sampler import SamplerConfig, sample_secrets


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--secrets",
        required=True,
        help="JSON object of key/value secrets to sample from",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help="Sampling rate between 0 (exclusive) and 1 (inclusive). Default: 1.0",
    )
    parser.add_argument(
        "--max-keys",
        type=int,
        default=None,
        dest="max_keys",
        help="Maximum number of keys to return",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible sampling",
    )


def run_sampler_command(args: argparse.Namespace) -> int:
    try:
        secrets = json.loads(args.secrets)
    except json.JSONDecodeError as exc:
        print(f"error: invalid secrets JSON — {exc}", file=sys.stderr)
        return 1

    config = SamplerConfig(rate=args.rate, max_keys=args.max_keys, seed=args.seed)
    try:
        result = sample_secrets(secrets, config)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.sampled, indent=2, sort_keys=True))
    print(
        f"# sampled {result.total_sampled}/{result.total_input} keys "
        f"({result.skipped} skipped)",
        file=sys.stderr,
    )
    return 0


def add_sampler_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("sampler", help="Sample a subset of secrets")
    _configure_parser(parser)
    parser.set_defaults(func=run_sampler_command)


def build_sampler_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sample secrets from a JSON map")
    _configure_parser(parser)
    return parser
