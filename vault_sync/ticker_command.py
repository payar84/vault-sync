from __future__ import annotations
import argparse
from vault_sync.ticker import TickerConfig, TickerState


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--interval", type=float, default=1.0, help="Tick interval in seconds")
    parser.add_argument("--max-ticks", type=int, default=None, help="Maximum number of ticks")
    parser.add_argument("action", choices=["run", "status"], nargs="?", default="run")


def run_ticker_command(args: argparse.Namespace) -> int:
    try:
        cfg = TickerConfig(interval_seconds=args.interval, max_ticks=args.max_ticks)
        cfg.validate()
    except ValueError as exc:
        print(f"[ticker] invalid config: {exc}")
        return 1

    state = TickerState(config=cfg)

    if args.action == "status":
        print(f"[ticker] interval={cfg.interval_seconds}s max_ticks={cfg.max_ticks}")
        return 0

    ticks_to_run = cfg.max_ticks if cfg.max_ticks is not None else 3
    for _ in range(ticks_to_run):
        event = state.tick()
        print(f"[ticker] tick={event.tick} at={event.fired_at}")
        if state.is_done():
            break

    print(f"[ticker] completed {state.count} tick(s)")
    return 0


def add_ticker_subcommand(subparsers) -> None:
    parser = subparsers.add_parser("ticker", help="Periodic tick scheduler")
    _configure_parser(parser)
    parser.set_defaults(func=run_ticker_command)


def build_ticker_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync ticker")
    _configure_parser(parser)
    return parser
