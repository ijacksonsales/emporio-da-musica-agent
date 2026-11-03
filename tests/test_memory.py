from datetime import datetime, timedelta, timezone

import pytest

from emporio_agent.memory import ConversationStore, new_session_id


class Clock:
    def __init__(self):
        self.now = datetime(2026, 3, 25, 12, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def memory(tmp_path, clock):
    return ConversationStore(tmp_path / "mem.sqlite3", ttl_days=7, clock=clock)


def test_round_trip_keeps_order(memory):
    sid = new_session_id()
    memory.append(sid, "user", "oi")
    memory.append(sid, "assistant", "Olá! Como posso ajudar?")
    assert [(m.role, m.text) for m in memory.load_history(sid)] == [
        ("user", "oi"),
        ("assistant", "Olá! Como posso ajudar?"),
    ]


def test_sessions_are_isolated(memory):
    a, b = new_session_id(), new_session_id()
    memory.append(a, "user", "mensagem de A")
    assert memory.load_history(b) == []


def test_history_expires_after_ttl_since_last_activity(memory, clock):
    sid = new_session_id()
    memory.append(sid, "user", "oi")
    clock.now += timedelta(days=6)
    memory.append(sid, "user", "voltei")  # activity renews the TTL
    clock.now += timedelta(days=6)
    assert len(memory.load_history(sid)) == 2
    clock.now += timedelta(days=2)
    assert memory.load_history(sid) == []


def test_history_is_limited_to_recent_messages(memory):
    sid = new_session_id()
    for i in range(30):
        memory.append(sid, "user", f"m{i}")
    history = memory.load_history(sid, limit=5)
    assert [m.text for m in history] == ["m25", "m26", "m27", "m28", "m29"]
