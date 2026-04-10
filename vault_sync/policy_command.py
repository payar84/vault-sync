"""CLI subcommand: vault-sync policy-check — validate a policy file and test a path/key."""
from __future__ import annotations

import argparse
import sys

from vault_sync.policy_loader import load_policy_file


def add_policy_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "policy-check",
        help="Validate a policy file and optionally test path/key access.",
    )
    _configure_parser(parser)


def build_policy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync policy-check")
    _configure_parser(parser)
    return parser


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("policy_file", help="Path to the policy JSON/YAML file.")
    parser.add_argument("--path", default=None, help="Vault secret path to test.")
    parser.add_argument("--key", default=None, help="Secret key name to test.")
    parser.set_defaults(func=run_policy_command)


def run_policy_command(args: argparse.Namespace) -> int:
    try:
        policy = load_policy_file(args.policy_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"[ok] Policy loaded — {len(policy.rules)} rule(s).")

    if args.path is None:
        return 0

    path_allowed = policy.is_path_allowed(args.path)
    status = "ALLOWED" if path_allowed else "DENIED"
    print(f"Path '{args.path}': {status}")

    if args.key is not None:
        if not path_allowed:
            print(f"Key '{args.key}': DENIED (path blocked)")
        else:
            key_allowed = policy.is_key_allowed(args.path, args.key)
            key_status = "ALLOWED" if key_allowed else "DENIED"
            print(f"Key '{args.key}': {key_status}")

    return 0
