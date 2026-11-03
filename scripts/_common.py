"""Shared helpers for the scripts that run the live agent."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from emporio_agent.agent import AgentReply  # noqa: E402
from emporio_agent.config import get_settings  # noqa: E402
from emporio_agent.memory import new_session_id  # noqa: E402
from emporio_agent.runtime import Runtime, build_runtime  # noqa: E402

PAUSE_BETWEEN_CALLS = 6  # seconds; free tier allows 15 requests per minute


def fresh_runtime(db_name: str) -> Runtime:
    """Runtime with its own SQLite file so script runs don't mix with real conversations."""
    db = ROOT / "var" / db_name
    db.unlink(missing_ok=True)
    return build_runtime(replace(get_settings(), db_path=db))


def run_conversation(runtime: Runtime, messages: list[str]) -> list[tuple[str, AgentReply]]:
    session = new_session_id()
    turns = []
    for message in messages:
        reply = runtime.chat(session, message)
        if reply.error:
            raise RuntimeError(f"LLM error on {message!r}: {reply.error}")
        turns.append((message, reply))
        time.sleep(PAUSE_BETWEEN_CALLS)
    return turns


def format_tools(reply: AgentReply) -> str:
    if not reply.tool_trace:
        return ""
    calls = ", ".join(
        f"`{t.call.name}({json.dumps(t.call.args, ensure_ascii=False)})`" for t in reply.tool_trace
    )
    return f"\n> 🔧 Tools called: {calls}\n"


def transcript(turns: list[tuple[str, AgentReply]], glosses: list[str] | None = None) -> str:
    """Markdown transcript. `glosses` are English translations of the customer messages."""
    lines = []
    for i, (message, reply) in enumerate(turns):
        gloss = f"  \n*(EN: {glosses[i]})*" if glosses else ""
        lines.append(f"**Customer:** {message}{gloss}\n")
        lines.append(format_tools(reply))
        lines.append(f"**Lia:** {reply.text}\n")
    return "\n".join(line for line in lines if line)
