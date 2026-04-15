"""CLI subcommand for semaphore demonstration and status."""
from __future__ import annotations

import argparse
import threading
import time
from typing import List

from vault_sync.semaphore import SemaphoreConfig, VaultSemaphore


def _configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-concurrent", type=int, default=4,
                        help="Maximum parallel operations (default: 4)")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="Seconds to wait for a slot (default: 30.0)")
    sub = parser.add_subparsers(dest="semaphore_action")
    demo = sub.add_parser("demo", help="Run a short concurrency demo")
    demo.add_argument("--tasks", type=int, default=6, help="Number of tasks to run")
    demo.add_argument("--task-duration", type=float, default=0.1)
    sub.add_parser("status", help="Print semaphore configuration")


def run_semaphore_command(args: argparse.Namespace) -> int:
    try:
        config = SemaphoreConfig(
            max_concurrent=args.max_concurrent,
            timeout=args.timeout,
        )
        config.validate()
    except ValueError as exc:
        print(f"[semaphore] invalid config: {exc}")
        return 1

    action = getattr(args, "semaphore_action", None)

    if action == "status" or action is None:
        print(f"[semaphore] max_concurrent={config.max_concurrent} timeout={config.timeout}s")
        return 0

    if action == "demo":
        sem = VaultSemaphore(config=config)
        results: List[str] = []
        lock = threading.Lock()

        def task(idx: int) -> None:
            result = sem.acquire()
            if not result.acquired:
                with lock:
                    results.append(f"task-{idx}: {result.reason}")
                return
            try:
                time.sleep(args.task_duration)
                with lock:
                    results.append(f"task-{idx}: done (active={sem.active})")
            finally:
                sem.release()

        threads = [threading.Thread(target=task, args=(i,)) for i in range(args.tasks)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for r in results:
            print(f"  {r}")
        return 0

    print(f"[semaphore] unknown action: {action}")
    return 1


def add_semaphore_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("semaphore", help="Manage concurrency semaphore")
    _configure_parser(parser)


def build_semaphore_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault-sync semaphore")
    _configure_parser(parser)
    return parser
