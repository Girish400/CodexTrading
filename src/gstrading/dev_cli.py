from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from gstrading.memory import MemoryConfig, MemoryStore
from gstrading.memory_cli import run_memory_exec


def add_dev_subcommands(subparsers: argparse._SubParsersAction) -> None:
    dev_parser = subparsers.add_parser(
        "dev",
        help=(
            "Developer wrapper for test, lint, build, "
            "and custom commands with auto memory capture."
        ),
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--project",
        default=Path.cwd().name,
        help="Logical project name. Defaults to the current directory name.",
    )
    common.add_argument(
        "--db-path",
        default=".gstrading/memory.db",
        help="SQLite database path for stored memory.",
    )
    common.add_argument(
        "--session-id",
        default=None,
        help=(
            "Optional explicit session id. If omitted, "
            "reuse the latest active session or create one."
        ),
    )
    common.add_argument(
        "--title",
        default=None,
        help="Optional title when a new session is created automatically.",
    )
    common.add_argument(
        "--objective",
        default=None,
        help="Optional objective when a new session is created automatically.",
    )
    common.add_argument(
        "--cwd",
        default=None,
        help="Optional working directory for wrapped commands.",
    )
    common.add_argument(
        "--close-session",
        action="store_true",
        help="Close the active session after the wrapped command finishes.",
    )

    dev_subparsers = dev_parser.add_subparsers(dest="dev_command", required=True)

    test_parser = dev_subparsers.add_parser(
        "test",
        parents=[common],
        help="Run pytest with memory capture.",
    )
    test_parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to pytest.",
    )

    lint_parser = dev_subparsers.add_parser(
        "lint",
        parents=[common],
        help="Run ruff with memory capture.",
    )
    lint_parser.add_argument(
        "ruff_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to ruff.",
    )

    build_parser = dev_subparsers.add_parser(
        "build",
        parents=[common],
        help="Run python -m build with memory capture.",
    )
    build_parser.add_argument(
        "build_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to build.",
    )

    run_parser = dev_subparsers.add_parser(
        "run",
        parents=[common],
        help="Run an arbitrary command with memory capture.",
    )
    run_parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help="Command to run after --, for example: -- python -m pytest tests/test_cli.py",
    )

    close_parser = dev_subparsers.add_parser(
        "close",
        parents=[common],
        help="Close the current or specified active developer session.",
    )
    close_parser.add_argument("--status", default="completed", help="Final status for the session.")

    brief_parser = dev_subparsers.add_parser(
        "brief",
        parents=[common],
        help="Show a future-session brief from the developer wrapper.",
    )
    brief_parser.add_argument(
        "--query",
        default="What should a future developer session know before continuing work?",
        help="Retrieval query for the brief.",
    )
    brief_parser.add_argument("--limit", type=int, default=3, help="Number of related summaries.")


def run_dev_command(args: argparse.Namespace) -> int:
    store = MemoryStore(MemoryConfig(project=args.project, database_path=args.db_path))
    if args.dev_command == "brief":
        brief = store.build_brief(query=args.query, limit=args.limit)
        print(brief.render())
        return 0

    if args.dev_command == "close":
        session = _resolve_session(store, args.session_id)
        if session is None:
            print("No active session found.")
            return 0
        closed = store.close_session(session.session_id, status=args.status)
        print(closed.summary_text or "")
        return 0

    session = _ensure_session(store, args)
    print(f"Using session {session.session_id}")
    return_code = _run_wrapped_command(store, session.session_id, args)
    if args.close_session:
        final_status = "completed" if return_code == 0 else "failed"
        closed = store.close_session(session.session_id, status=final_status)
        print(closed.summary_text or "")
    return return_code


def _resolve_session(store: MemoryStore, session_id: str | None):
    if session_id:
        return store._row_to_session(store._fetch_session_row(session_id))
    return store.get_active_session()


def _ensure_session(store: MemoryStore, args: argparse.Namespace):
    if args.session_id:
        return store._row_to_session(store._fetch_session_row(args.session_id))
    title = args.title or f"Developer workflow {datetime.utcnow().date().isoformat()}"
    objective = args.objective or "Capture developer test, lint, build, and tooling activity."
    session, created = store.get_or_create_active_session(title=title, objective=objective)
    if created:
        print(f"Started session {session.session_id}")
    return session


def _run_wrapped_command(store: MemoryStore, session_id: str, args: argparse.Namespace) -> int:
    command_args: list[str]
    if args.dev_command == "test":
        extras = _strip_remainder(args.pytest_args)
        command_args = [sys.executable, "-m", "pytest", *extras]
    elif args.dev_command == "lint":
        extras = _strip_remainder(args.ruff_args)
        if not extras:
            extras = ["."]
        command_args = [sys.executable, "-m", "ruff", "check", *extras]
    elif args.dev_command == "build":
        extras = _strip_remainder(args.build_args)
        command_args = [sys.executable, "-m", "build", *extras]
    elif args.dev_command == "run":
        command_args = _strip_remainder(args.command_args)
        if not command_args:
            raise ValueError("dev run requires a command after --")
    else:
        raise ValueError(f"Unsupported dev command: {args.dev_command}")

    return run_memory_exec(
        store=store,
        session_id=session_id,
        command_args=command_args,
        cwd=args.cwd,
        tags={"dev-wrapper", args.dev_command},
    )


def _strip_remainder(items: list[str]) -> list[str]:
    if items and items[0] == "--":
        return items[1:]
    return items
