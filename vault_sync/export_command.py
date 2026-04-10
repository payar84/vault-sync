"""CLI helper that wires the exporter into the vault-sync command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

from vault_sync.exporter import ExportFormat, export_secrets, parse_export_format


def add_export_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'export' sub-command onto an existing subparsers object."""
    parser = subparsers.add_parser(
        "export",
        help="Export secrets to a file or stdout in a chosen format",
    )
    parser.add_argument(
        "--format",
        dest="export_format",
        default="dotenv",
        metavar="FORMAT",
        help="Output format: dotenv (default), json, yaml",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    parser.set_defaults(func=run_export_command)


def run_export_command(
    args: argparse.Namespace,
    secrets: Optional[Dict[str, str]] = None,
) -> int:
    """Execute the export command.  Returns an exit code."""
    try:
        fmt = parse_export_format(args.export_format)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if secrets is None:
        secrets = {}

    output_path: Optional[Path] = None
    if args.output_path:
        output_path = Path(args.output_path)

    content = export_secrets(secrets, fmt, output_path=output_path)

    if output_path is None:
        sys.stdout.write(content)
    else:
        print(f"Exported {len(secrets)} secret(s) to {output_path} [{fmt.value}]")

    return 0


def build_export_parser() -> argparse.ArgumentParser:
    """Standalone parser for the export command (useful for testing)."""
    parser = argparse.ArgumentParser(prog="vault-sync export")
    parser.add_argument("--format", dest="export_format", default="dotenv")
    parser.add_argument("--output", dest="output_path", default=None)
    return parser
