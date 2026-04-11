"""CLI subcommand for tag-based secret inspection."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

from vault_sync.tags import TagSet, filter_by_tags, group_by_tag, parse_tags


def _build_sample_registry() -> Dict[str, TagSet]:
    """Return a demo registry; real usage would load from a config or cache."""
    return {
        "secret/app/db": TagSet({"env": "prod", "team": "backend"}),
        "secret/app/cache": TagSet({"env": "prod", "team": "backend"}),
        "secret/app/email": TagSet({"env": "staging", "team": "backend"}),
        "secret/infra/vpn": TagSet({"env": "prod", "team": "infra"}),
        "secret/infra/dns": TagSet({"team": "infra"}),
    }


def run_tags_command(args: argparse.Namespace) -> int:
    registry = _build_sample_registry()

    if args.tags_action == "filter":
        try:
            required = parse_tags(args.match)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        paths = filter_by_tags(registry, required)
        if not paths:
            print("No secrets matched the given tags.")
        else:
            for p in paths:
                print(p)
        return 0

    if args.tags_action == "group":
        groups = group_by_tag(registry, args.key)
        print(json.dumps(groups, indent=2))
        return 0

    print(f"Unknown tags action: {args.tags_action}", file=sys.stderr)
    return 1


def _configure_parser(sub: argparse.ArgumentParser) -> None:
    actions = sub.add_subparsers(dest="tags_action")

    filt = actions.add_parser("filter", help="Filter secrets by tags")
    filt.add_argument(
        "--match",
        required=True,
        metavar="KEY=VALUE,...",
        help="Comma-separated tag expressions, e.g. env=prod,team=backend",
    )

    grp = actions.add_parser("group", help="Group secrets by a tag key")
    grp.add_argument(
        "--key",
        required=True,
        metavar="TAG_KEY",
        help="Tag key to group by, e.g. env",
    )


def add_tags_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "tags",
        help="Filter or group secrets by metadata tags",
    )
    _configure_parser(parser)
    parser.set_defaults(func=run_tags_command)


def build_tags_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync tags")
    _configure_parser(parser)
    return parser
