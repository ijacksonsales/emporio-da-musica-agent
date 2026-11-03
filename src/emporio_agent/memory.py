"""Conversation history in SQLite with a time-to-live (decision D06).

Only user and assistant messages are stored; raw tool results are not, so the history
sent to the model stays small (D02) and personal data returned by tools is not kept.
Expiry counts from the session's last activity, using the real clock.
"""

from __future__ import annotations

import re
import sqlite3
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from emporio_agent.llm.base import Message

SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")
MAX_HISTORY_MESSAGES = 20


def new_session_id() -> str:
    return str(uuid.uuid4())


def is_valid_session_id(session_id: str | None) -> bool:
    return bool(session_id) and bool(SESSION_ID_PATTERN.fullmatch(session_id))


class ConversationStore:
    def __init__(
        self,
        db_path: Path,
        ttl_days: int = 7,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.ttl = timedelta(days=ttl_days)
        self.clock = clock
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _cutoff(self) -> str:
        return (self.clock() - self.ttl).isoformat()

    def purge_expired(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE last_activity < ?", (self._cutoff(),))
            return cur.rowcount

    def load_history(self, session_id: str, limit: int = MAX_HISTORY_MESSAGES) -> list[Message]:
        if not is_valid_session_id(session_id):
            return []
        self.purge_expired()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, text FROM ("
                "  SELECT id, role, text FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?"
                ") ORDER BY id",
                (session_id, limit),
            ).fetchall()
        return [Message(role=role, text=text) for role, text in rows]

    def append(self, session_id: str, role: str, text: str) -> None:
        if not is_valid_session_id(session_id):
            raise ValueError("invalid session id")
        now = self.clock().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, created_at, last_activity) VALUES (?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET last_activity = excluded.last_activity",
                (session_id, now, now),
            )
            conn.execute(
                "INSERT INTO messages (session_id, role, text, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, text, now),
            )
