from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Set

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./:-]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 1]


def extract_file_refs(text: str) -> list[str]:
    return sorted(
        {
            token
            for token in TOKEN_PATTERN.findall(text)
            if "/" in token or token.endswith((".py", ".md", ".yml", ".yaml", ".toml", ".json"))
        }
    )


def semantic_weights(text: str) -> dict[str, float]:
    counts = Counter(tokenize(text))
    total = sum(counts.values()) or 1
    return {token: count / total for token, count in counts.items()}


def semantic_score(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    return sum(left[token] * right[token] for token in shared)


@dataclass(slots=True, frozen=True)
class MemoryConfig:
    project: str
    database_path: str = ".gstrading/memory.db"

    @property
    def database_file(self) -> Path:
        return Path(self.database_path)


@dataclass(slots=True, frozen=True)
class SessionRecord:
    session_id: str
    project: str
    title: str
    objective: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    summary_text: Optional[str] = None


@dataclass(slots=True, frozen=True)
class ObservationRecord:
    observation_id: int
    session_id: str
    observed_at: str
    tool_name: str
    kind: str
    content: str
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class SummaryRecord:
    summary_id: int
    session_id: str
    project: str
    created_at: str
    summary_text: str
    semantic_terms: dict[str, float]


@dataclass(slots=True, frozen=True)
class ProjectBrief:
    project: str
    query: str
    generated_at: str
    latest_summary: Optional[str]
    pinned_facts: tuple[str, ...]
    relevant_summaries: tuple[str, ...]
    open_items: tuple[str, ...]

    def render(self) -> str:
        lines = [
            f"Project: {self.project}",
            f"Generated At: {self.generated_at}",
            f"Query: {self.query}",
        ]
        if self.latest_summary:
            lines.append("Latest Summary:")
            lines.append(self.latest_summary)
        if self.pinned_facts:
            lines.append("Pinned Facts:")
            lines.extend(f"- {item}" for item in self.pinned_facts)
        if self.relevant_summaries:
            lines.append("Relevant Summaries:")
            lines.extend(f"- {item}" for item in self.relevant_summaries)
        if self.open_items:
            lines.append("Open Items:")
            lines.extend(f"- {item}" for item in self.open_items)
        return "\n".join(lines)


class MemoryStore:
    def __init__(self, config: MemoryConfig) -> None:
        self.config = config
        self._initialize()

    def start_session(self, title: str, objective: str) -> SessionRecord:
        session_id = uuid.uuid4().hex
        started_at = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (
                    session_id, project, title, objective, status, started_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.config.project,
                    normalize_text(title),
                    normalize_text(objective),
                    "active",
                    started_at,
                    started_at,
                ),
            )
        return SessionRecord(
            session_id=session_id,
            project=self.config.project,
            title=normalize_text(title),
            objective=normalize_text(objective),
            status="active",
            started_at=started_at,
        )

    def get_active_session(self) -> Optional[SessionRecord]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    session_id,
                    project,
                    title,
                    objective,
                    status,
                    started_at,
                    ended_at,
                    summary_text
                FROM sessions
                WHERE project = ? AND status = 'active'
                ORDER BY updated_at DESC, started_at DESC
                LIMIT 1
                """,
                (self.config.project,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_session(row)

    def get_or_create_active_session(
        self,
        title: str,
        objective: str,
    ) -> tuple[SessionRecord, bool]:
        active = self.get_active_session()
        if active is not None:
            return active, False
        return self.start_session(title=title, objective=objective), True

    def record_observation(
        self,
        session_id: str,
        tool_name: str,
        kind: str,
        content: str,
        tags: Optional[Set[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ObservationRecord:
        observed_at = utc_now()
        normalized_content = normalize_text(content)
        raw_tags = tuple(sorted(tags or set()))
        raw_metadata = metadata or {}
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO observations (
                    session_id, observed_at, tool_name, kind, content, tags_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    observed_at,
                    normalize_text(tool_name),
                    normalize_text(kind),
                    normalized_content,
                    json.dumps(raw_tags),
                    json.dumps(raw_metadata, sort_keys=True),
                ),
            )
            observation_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (observed_at, session_id),
            )
        return ObservationRecord(
            observation_id=observation_id,
            session_id=session_id,
            observed_at=observed_at,
            tool_name=normalize_text(tool_name),
            kind=normalize_text(kind),
            content=normalized_content,
            tags=raw_tags,
            metadata=raw_metadata,
        )

    def pin_fact(self, category: str, content: str) -> None:
        timestamp = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pinned_facts (project, category, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self.config.project,
                    normalize_text(category),
                    normalize_text(content),
                    timestamp,
                    timestamp,
                ),
            )

    def add_open_item(self, session_id: str, content: str, status: str = "open") -> None:
        timestamp = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO open_items (
                    project, session_id, content, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self.config.project,
                    session_id,
                    normalize_text(content),
                    normalize_text(status),
                    timestamp,
                    timestamp,
                ),
            )

    def close_session(self, session_id: str, status: str = "completed") -> SessionRecord:
        session_row = self._fetch_session_row(session_id)
        observations = self.list_observations(session_id)
        summary_text = self._generate_summary(session_row, observations)
        semantic_terms = semantic_weights(summary_text)
        ended_at = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE sessions
                SET status = ?, ended_at = ?, summary_text = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (normalize_text(status), ended_at, summary_text, ended_at, session_id),
            )
            connection.execute(
                """
                INSERT INTO summaries (
                    session_id, project, created_at, summary_text, semantic_terms_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.config.project,
                    ended_at,
                    summary_text,
                    json.dumps(semantic_terms, sort_keys=True),
                ),
            )
        return SessionRecord(
            session_id=session_id,
            project=self.config.project,
            title=session_row["title"],
            objective=session_row["objective"],
            status=normalize_text(status),
            started_at=session_row["started_at"],
            ended_at=ended_at,
            summary_text=summary_text,
        )

    def build_brief(self, query: str, limit: int = 3) -> ProjectBrief:
        normalized_query = normalize_text(query)
        query_terms = semantic_weights(normalized_query)
        summaries = self.list_summaries()
        latest_summary = summaries[0].summary_text if summaries else None
        ranked = sorted(
            summaries,
            key=lambda record: (
                semantic_score(query_terms, record.semantic_terms),
                record.created_at,
            ),
            reverse=True,
        )
        relevant = tuple(record.summary_text for record in ranked[:limit] if record.summary_text)
        pinned_facts = self.list_pinned_facts()
        open_items = self.list_open_items()
        return ProjectBrief(
            project=self.config.project,
            query=normalized_query,
            generated_at=utc_now(),
            latest_summary=latest_summary,
            pinned_facts=tuple(pinned_facts),
            relevant_summaries=relevant,
            open_items=tuple(open_items),
        )

    def list_observations(self, session_id: str) -> list[ObservationRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT observation_id, session_id, observed_at, tool_name, kind, content,
                       tags_json, metadata_json
                FROM observations
                WHERE session_id = ?
                ORDER BY observation_id ASC
                """,
                (session_id,),
            ).fetchall()
        return [
            ObservationRecord(
                observation_id=int(row["observation_id"]),
                session_id=row["session_id"],
                observed_at=row["observed_at"],
                tool_name=row["tool_name"],
                kind=row["kind"],
                content=row["content"],
                tags=tuple(json.loads(row["tags_json"])),
                metadata=json.loads(row["metadata_json"]),
            )
            for row in rows
        ]

    def list_summaries(self) -> list[SummaryRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    summary_id,
                    session_id,
                    project,
                    created_at,
                    summary_text,
                    semantic_terms_json
                FROM summaries
                WHERE project = ?
                ORDER BY created_at DESC
                """,
                (self.config.project,),
            ).fetchall()
        return [
            SummaryRecord(
                summary_id=int(row["summary_id"]),
                session_id=row["session_id"],
                project=row["project"],
                created_at=row["created_at"],
                summary_text=row["summary_text"],
                semantic_terms=json.loads(row["semantic_terms_json"]),
            )
            for row in rows
        ]

    def list_pinned_facts(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT category, content
                FROM pinned_facts
                WHERE project = ?
                ORDER BY updated_at DESC, pinned_fact_id DESC
                """,
                (self.config.project,),
            ).fetchall()
        return [f"[{row['category']}] {row['content']}" for row in rows]

    def list_open_items(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT content, status
                FROM open_items
                WHERE project = ? AND status != 'closed'
                ORDER BY updated_at DESC, open_item_id DESC
                """,
                (self.config.project,),
            ).fetchall()
        return [f"[{row['status']}] {row['content']}" for row in rows]

    def _fetch_session_row(self, session_id: str) -> sqlite3.Row:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    session_id,
                    project,
                    title,
                    objective,
                    status,
                    started_at,
                    ended_at,
                    summary_text
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Unknown session id: {session_id}")
        return row

    def _row_to_session(self, row: sqlite3.Row) -> SessionRecord:
        return SessionRecord(
            session_id=row["session_id"],
            project=row["project"],
            title=row["title"],
            objective=row["objective"],
            status=row["status"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            summary_text=row["summary_text"],
        )

    def _generate_summary(
        self,
        session_row: sqlite3.Row,
        observations: list[ObservationRecord],
    ) -> str:
        if not observations:
            return (
                f"Objective: {session_row['objective']}. "
                "No tool observations were captured during this session."
            )

        tools = sorted({observation.tool_name for observation in observations})
        files = sorted(
            {
                file_ref
                for observation in observations
                for file_ref in extract_file_refs(observation.content)
            }
        )
        errors = [
            observation.content
            for observation in observations
            if observation.kind.lower() in {"error", "failure"}
        ]
        commands = [
            observation.content
            for observation in observations
            if observation.kind.lower() in {"command", "test", "build"}
        ]

        summary_parts = [
            f"Objective: {session_row['objective']}.",
            f"Captured {len(observations)} observations across tools: {', '.join(tools)}.",
        ]
        if files:
            summary_parts.append(f"Key files: {', '.join(files[:8])}.")
        if commands:
            summary_parts.append(f"Notable commands: {' | '.join(commands[:3])}.")
        if errors:
            summary_parts.append(f"Observed issues: {' | '.join(errors[:2])}.")
        else:
            summary_parts.append("No explicit failures were recorded in the observation log.")
        return " ".join(summary_parts)

    def _initialize(self) -> None:
        self.config.database_file.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    project TEXT NOT NULL,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    summary_text TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS observations (
                    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS summaries (
                    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    project TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    semantic_terms_json TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS pinned_facts (
                    pinned_fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS open_items (
                    open_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.config.database_file)
        connection.row_factory = sqlite3.Row
        return connection
