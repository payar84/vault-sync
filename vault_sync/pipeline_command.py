"""CLI subcommand: vault-sync pipeline — preview a secret pipeline run."""
from __future__ import annotations

import argparse
import json
from typing import List

from vault_sync.pipeline import PipelineConfig, PipelineResult, run_pipeline
from vault_sync.filter import FilterConfig, parse_patterns
from vault_sync.transform import strip_whitespace, to_uppercase_value, mask_sensitive
from vault_sync.alias import AliasMap


_TRANSFORM_MAP = {
    "strip": strip_whitespace,
    "uppercase": to_uppercase_value,
    "mask": mask_sensitive,
}


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--secrets", required=True, help="JSON string of key=value secrets")
    parser.add_argument("--include", nargs="*", default=[], metavar="PATTERN")
    parser.add_argument("--exclude", nargs="*", default=[], metavar="PATTERN")
    parser.add_argument(
        "--transform", nargs="*", default=[],
        choices=list(_TRANSFORM_MAP.keys()), metavar="TRANSFORM"
    )
    parser.add_argument("--aliases", default="{}", help="JSON object mapping old->new key names")


def run_pipeline_command(args: argparse.Namespace) -> int:
    try:
        secrets = json.loads(args.secrets)
    except json.JSONDecodeError as exc:
        print(f"error: invalid --secrets JSON: {exc}")
        return 1

    try:
        alias_data = json.loads(args.aliases)
    except json.JSONDecodeError as exc:
        print(f"error: invalid --aliases JSON: {exc}")
        return 1

    filter_cfg = FilterConfig(
        include_prefixes=parse_patterns(args.include),
        exclude_patterns=parse_patterns(args.exclude),
    ) if (args.include or args.exclude) else None

    transforms = [_TRANSFORM_MAP[t] for t in (args.transform or [])]
    alias_map = AliasMap(aliases=alias_data) if alias_data else None

    config = PipelineConfig(
        filter_config=filter_cfg,
        transforms=transforms,
        alias_map=alias_map,
    )

    result: PipelineResult = run_pipeline(secrets, config)
    print(result)
    print(json.dumps(result.secrets, indent=2, sort_keys=True))
    if result.dropped:
        print(f"dropped: {result.dropped}")
    if result.renamed:
        print(f"renamed: {result.renamed}")
    return 0


def add_pipeline_subcommand(subparsers) -> None:
    parser = subparsers.add_parser("pipeline", help="Preview a secret pipeline run")
    _configure_parser(parser)
    parser.set_defaults(func=run_pipeline_command)


def build_pipeline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync pipeline")
    _configure_parser(parser)
    return parser
