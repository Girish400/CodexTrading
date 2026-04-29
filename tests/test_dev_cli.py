import argparse
import sqlite3
import sys

from codextrading.dev_cli import run_dev_command


def test_dev_run_creates_and_reuses_active_session(tmp_path, capsys) -> None:
    db_path = tmp_path / "memory.db"

    first_args = argparse.Namespace(
        command="dev",
        dev_command="run",
        project="CodexTrading",
        db_path=str(db_path),
        session_id=None,
        title="Dev wrapper test",
        objective="Capture developer wrapper usage.",
        cwd=None,
        close_session=False,
        command_args=["--", sys.executable, "-c", "print('dev one')"],
    )
    second_args = argparse.Namespace(
        command="dev",
        dev_command="run",
        project="CodexTrading",
        db_path=str(db_path),
        session_id=None,
        title="Ignored because active session exists",
        objective="Ignored because active session exists",
        cwd=None,
        close_session=True,
        command_args=["--", sys.executable, "-c", "print('dev two')"],
    )

    assert run_dev_command(first_args) == 0
    assert run_dev_command(second_args) == 0
    output = capsys.readouterr().out

    assert "Started session" in output
    assert "Using session" in output
    assert "dev one" in output
    assert "dev two" in output

    with sqlite3.connect(db_path) as connection:
        sessions = connection.execute("SELECT status FROM sessions").fetchall()
        observations = connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0]

    assert len(sessions) == 1
    assert sessions[0][0] == "completed"
    assert observations == 2
