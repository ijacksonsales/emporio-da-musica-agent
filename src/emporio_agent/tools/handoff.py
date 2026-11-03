"""Human handoff: register complaints and cases the agent must not resolve alone.

Manual §7.3: listen with empathy, register the complaint and forward it; the team
replies within 24 business hours.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from emporio_agent.tools import ToolError

REASONS = {"reclamacao", "problema_pedido", "duvida_valor", "seguranca", "outro"}
MAX_SUMMARY_LENGTH = 1000


class HandoffStore:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS handoffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    order_id INTEGER,
                    created_at TEXT NOT NULL
                )"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:  # commit or roll back
                yield conn
        finally:
            conn.close()

    def create(self, session_id: str, reason: str, summary: str, order_id: int | None) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO handoffs (session_id, reason, summary, order_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, reason, summary, order_id, datetime.now(timezone.utc).isoformat()),
            )
            return int(cur.lastrowid)

    def count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM handoffs").fetchone()[0]


def escalate_to_human(
    handoffs: HandoffStore,
    session_id: str,
    reason: str,
    summary: str,
    order_id: int | str | None = None,
) -> dict:
    if reason not in REASONS:
        raise ToolError(f"reason inválido; use um de: {', '.join(sorted(REASONS))}")
    summary = (summary or "").strip()
    if not summary:
        raise ToolError("descreva o caso em summary")
    if len(summary) > MAX_SUMMARY_LENGTH:
        summary = summary[:MAX_SUMMARY_LENGTH]
    parsed_order = None
    if order_id not in (None, ""):
        text = str(order_id).strip().lstrip("#")
        if not text.isdigit() or len(text) > 9:
            raise ToolError("order_id deve ser o número do pedido")
        parsed_order = int(text)

    ticket = handoffs.create(session_id, reason, summary, parsed_order)
    return {
        "registrado": True,
        "protocolo": f"EMP-{ticket:06d}",
        "prazo_retorno": "até 24 horas úteis",
        "observacao": "Informe o protocolo ao cliente e diga que a equipe vai retornar.",
    }
