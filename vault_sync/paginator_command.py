from __future__ import annotations
import argparse
import json
from vault_sync.paginator import PaginatorConfig, paginate


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument(
        "--keys",
        default=None,
        help="JSON array of keys to paginate (demo mode)",
    )


def run_paginator_command(args: argparse.Namespace) -> int:
    try:
        cfg = PaginatorConfig(page_size=args.page_size, max_pages=args.max_pages)
        cfg.validate()
    except ValueError as exc:
        print(f"[error] {exc}")
        return 1

    if args.keys:
        try:
            all_keys = json.loads(args.keys)
        except json.JSONDecodeError:
            print("[error] --keys must be a valid JSON array")
            return 1
    else:
        all_keys = [f"secret/key/{i}" for i in range(35)]

    def fetch(offset: int, limit: int) -> list:
        return all_keys[offset : offset + limit]

    result = paginate(fetch, cfg)
    print(repr(result))
    for page in result.pages:
        print(f"  {page}  items={page.items}")
    return 0


def add_paginator_subcommand(subparsers) -> None:
    parser = subparsers.add_parser("paginator", help="paginate secret paths")
    _configure_parser(parser)
    parser.set_defaults(func=run_paginator_command)


def build_paginator_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync paginator")
    _configure_parser(parser)
    return parser
