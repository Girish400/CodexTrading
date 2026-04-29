import sqlite3

from gstrading.memory import MemoryConfig, MemoryStore


def test_memory_store_generates_summary_and_brief(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    store = MemoryStore(MemoryConfig(project="GSTrading", database_path=str(db_path)))

    session = store.start_session(
        title="Session continuity",
        objective="Capture tool observations and prepare a future-session brief.",
    )
    store.record_observation(
        session_id=session.session_id,
        tool_name="pytest",
        kind="test",
        content="Ran pytest against tests/test_memory.py and tests/test_cli.py successfully.",
        tags={"tests", "verification"},
    )
    store.record_observation(
        session_id=session.session_id,
        tool_name="git",
        kind="command",
        content="Updated src/gstrading/memory.py and docs/session_memory.md.",
        tags={"git", "files"},
    )
    store.pin_fact(
        category="architecture",
        content="Session memory is stored in SQLite and ranked with semantic token overlap.",
    )
    store.add_open_item(
        session_id=session.session_id,
        content="Integrate automatic observation capture for shell command wrappers.",
    )
    closed = store.close_session(session.session_id)

    assert "Capture tool observations" in (closed.summary_text or "")

    brief = store.build_brief(query="How do I continue work on semantic session memory?")
    assert brief.latest_summary is not None
    assert brief.pinned_facts
    assert brief.relevant_summaries
    assert brief.open_items


def test_memory_store_creates_expected_tables(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    MemoryStore(MemoryConfig(project="GSTrading", database_path=str(db_path)))

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {"sessions", "observations", "summaries", "pinned_facts", "open_items"} <= tables
