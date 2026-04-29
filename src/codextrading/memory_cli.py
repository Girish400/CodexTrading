from __future__ import annotations

import argparse
import json
import subprocess

from codextrading.memory import MemoryConfig, MemoryStore


def add_memory_subcommands(subparsers: argparse._SubParsersAction) -> None:
    memory_parser = subparsers.add_parser(
        "memory",
        help="Manage cross-session project memory, observations, and summaries.",
    )
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", required=True, help="Logical project name.")
    common.add_argument(
        "--db-path",
        default=".codextrading/memory.db",
        help="SQLite database path for stored memory.",
    )

    start_parser = memory_subparsers.add_parser("start", parents=[common], help="Start a session.")
    start_parser.add_argument("--title", required=True, help="Short session title.")
    start_parser.add_argument("--objective", required=True, help="Session objective.")

    observe_parser = memory_subparsers.add_parser(
        "observe",
        parents=[common],
        help="Record a tool usage observation.",
    )
    observe_parser.add_argument("--session-id", required=True, help="Target session identifier.")
    observe_parser.add_argument("--tool", required=True, help="Tool or subsystem name.")
    observe_parser.add_argument("--kind", required=True, help="Observation type.")
    observe_parser.add_argument("--content", required=True, help="Observation content.")
    observe_parser.add_argument("--tags", nargs="*", default=[], help="Optional tags.")
    observe_parser.add_argument(
        "--metadata-json",
        default="{}",
        help="Optional JSON metadata payload.",
    )

    exec_parser = memory_subparsers.add_parser(
        "exec",
        parents=[common],
        help="Run a command and automatically capture the observation.",
    )
    exec_parser.add_argument("--session-id", required=True, help="Target session identifier.")
    exec_parser.add_argument(
        "--cwd",
        default=None,
        help="Optional working directory for the command.",
    )
    exec_parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help="Command to run after --, for example: -- python -m pytest",
    )

    pin_parser = memory_subparsers.add_parser(
        "pin",
        parents=[common],
        help="Pin a durable project fact.",
    )
    pin_parser.add_argument("--category", required=True, help="Fact category.")
    pin_parser.add_argument("--content", required=True, help="Fact content.")

    open_item_parser = memory_subparsers.add_parser(
        "open-item",
        parents=[common],
        help="Record an open item for future sessions.",
    )
    open_item_parser.add_argument("--session-id", required=True, help="Target session identifier.")
    open_item_parser.add_argument("--content", required=True, help="Open work item.")
    open_item_parser.add_argument("--status", default="open", help="Open item status.")

    close_parser = memory_subparsers.add_parser(
        "close",
        parents=[common],
        help="Close a session and generate a semantic summary.",
    )
    close_parser.add_argument("--session-id", required=True, help="Target session identifier.")
    close_parser.add_argument("--status", default="completed", help="Final session status.")

    brief_parser = memory_subparsers.add_parser(
        "brief",
        parents=[common],
        help="Build a future-session working brief.",
    )
    brief_parser.add_argument("--query", required=True, help="What the next session needs.")
    brief_parser.add_argument("--limit", type=int, default=3, help="Number of related summaries.")


def run_memory_exec(
    store: MemoryStore,
    session_id: str,
    command_args: list[str],
    cwd: str | None = None,
    tags: set[str] | None = None,
) -> int:
    completed = subprocess.run(
        command_args,
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )
    combined_output = "\n".join(
        part.strip() for part in [completed.stdout, completed.stderr] if part.strip()
    )
    output_excerpt = combined_output[:500] if combined_output else "No output captured."
    kind = "command" if completed.returncode == 0 else "failure"
    store.record_observation(
        session_id=session_id,
        tool_name=command_args[0],
        kind=kind,
        content=f"Ran {' '.join(command_args)}. Output: {output_excerpt}",
        tags={"auto-captured", "command", *(tags or set())},
        metadata={
            "returncode": completed.returncode,
            "cwd": cwd,
            "command": command_args,
        },
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="")
    return int(completed.returncode)


def run_memory_command(args: argparse.Namespace) -> int:
    store = MemoryStore(
        MemoryConfig(
            project=args.project,
            database_path=args.db_path,
        )
    )
    if args.memory_command == "start":
        session = store.start_session(title=args.title, objective=args.objective)
        print(session.session_id)
        return 0

    if args.memory_command == "observe":
        metadata = json.loads(args.metadata_json)
        observation = store.record_observation(
            session_id=args.session_id,
            tool_name=args.tool,
            kind=args.kind,
            content=args.content,
            tags=set(args.tags),
            metadata=metadata,
        )
        print(observation.observation_id)
        return 0

    if args.memory_command == "pin":
        store.pin_fact(category=args.category, content=args.content)
        print("pinned")
        return 0

    if args.memory_command == "exec":
        command_args = list(args.command_args)
        if command_args and command_args[0] == "--":
            command_args = command_args[1:]
        if not command_args:
            raise ValueError("memory exec requires a command after --")
        return run_memory_exec(
            store=store,
            session_id=args.session_id,
            command_args=command_args,
            cwd=args.cwd,
        )

    if args.memory_command == "open-item":
        store.add_open_item(
            session_id=args.session_id,
            content=args.content,
            status=args.status,
        )
        print("tracked")
        return 0

    if args.memory_command == "close":
        session = store.close_session(session_id=args.session_id, status=args.status)
        print(session.summary_text or "")
        return 0

    if args.memory_command == "brief":
        brief = store.build_brief(query=args.query, limit=args.limit)
        print(brief.render())
        return 0

    raise ValueError(f"Unsupported memory command: {args.memory_command}")
