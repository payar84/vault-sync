"""CLI subcommand: vault-sync template — render a .env template with Vault secrets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from vault_sync.client import VaultClient
from vault_sync.config import VaultConfig
from vault_sync.namespace import parse_namespaces
from vault_sync.template import collect_placeholders, render_template_file


def add_template_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'template' subcommand on an existing subparsers object."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "template",
        help="Render a .env template file using secrets fetched from Vault.",
    )
    parser.add_argument("template", type=Path, help="Path to the template file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Destination file for rendered output (default: stdout).",
    )
    parser.add_argument(
        "--namespaces",
        default="",
        help="Comma-separated namespace definitions (path:prefix).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rendered content without writing to disk.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any placeholder cannot be resolved.",
    )
    parser.set_defaults(func=run_template_command)


def _fetch_secrets(config: VaultConfig, namespace_arg: str) -> dict[str, str]:
    """Fetch secrets for all configured namespaces and merge into one dict."""
    client = VaultClient(config)
    namespaces = parse_namespaces(namespace_arg) if namespace_arg else []
    merged: dict[str, str] = {}
    for ns in namespaces:
        raw = client.read_secret(ns.path) or {}
        for k, v in raw.items():
            merged[ns.format_key(k)] = str(v)
    return merged


def run_template_command(args: argparse.Namespace) -> int:
    """Entry point for the template subcommand. Returns an exit code."""
    template_path: Path = args.template
    output_path: Optional[Path] = None if args.dry_run else args.output

    if not template_path.exists():
        print(f"error: template file not found: {template_path}", file=sys.stderr)
        return 1

    try:
        config = VaultConfig.from_env()
        config.validate()
    except Exception as exc:  # noqa: BLE001
        print(f"error: vault config invalid — {exc}", file=sys.stderr)
        return 1

    secrets = _fetch_secrets(config, getattr(args, "namespaces", ""))

    # Warn about placeholders that have no matching secret before rendering.
    placeholders = collect_placeholders(template_path.read_text(encoding="utf-8"))
    unresolvable = [p for p in placeholders if p not in secrets]
    if unresolvable:
        print(
            f"warning: {len(unresolvable)} placeholder(s) cannot be resolved: "
            + ", ".join(unresolvable),
            file=sys.stderr,
        )

    result = render_template_file(template_path, secrets, output_path=output_path)

    if args.dry_run:
        print(result.rendered)

    if args.strict and not result.ok:
        print(
            f"error: strict mode — {len(result.missing)} unresolved placeholder(s).",
            file=sys.stderr,
        )
        return 2

    return 0


def build_template_parser() -> argparse.ArgumentParser:
    """Build a standalone argument parser for the template subcommand."""
    parser = argparse.ArgumentParser(
        prog="vault-sync template",
        description="Render a .env template file using Vault secrets.",
    )
    subparsers = parser.add_subparsers()
    add_template_subcommand(subparsers)
    return parser
