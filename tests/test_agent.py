"""Agent loop tests with a scripted fake provider (no network)."""

from datetime import date

import pytest

from emporio_agent.agent import FALLBACK_REPLY, Agent, build_system_prompt
from emporio_agent.llm.base import LLMError, LLMResponse, ToolCall
from emporio_agent.tools.handoff import HandoffStore


class ScriptedTurn:
    def __init__(self, responses):
        self.responses = list(responses)
        self.received = []

    def next(self, tool_results=None):
        self.received.append(tool_results)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeProvider:
    def __init__(self, responses):
        self.turn = ScriptedTurn(responses)
        self.system_prompt = None

    def begin_turn(self, system_prompt, history, user_message, tools):
        self.system_prompt = system_prompt
        return self.turn


@pytest.fixture
def make_agent(store, tmp_path):
    def _make(responses):
        provider = FakeProvider(responses)
        agent = Agent(provider, store, date(2026, 3, 25), HandoffStore(tmp_path / "db.sqlite3"))
        return agent, provider

    return _make


def test_executes_tools_and_returns_final_text(make_agent):
    agent, provider = make_agent([
        LLMResponse(tool_calls=[ToolCall("get_product_details", {"product": "Takamine GD20"})]),
        LLMResponse(text="O Takamine GD20 sai por R$ 2.199,00."),
    ])
    reply = agent.respond("s1", [], "Quanto custa o Takamine GD20?")
    assert reply.text.startswith("O Takamine")
    assert reply.tool_trace[0].result["id"] == 95
    assert provider.turn.received[1][0].call.name == "get_product_details"


def test_tool_errors_go_back_to_the_model(make_agent):
    agent, _ = make_agent([
        LLMResponse(tool_calls=[ToolCall("get_store_policy", {"topic": "secrets"})]),
        LLMResponse(text="ok"),
    ])
    reply = agent.respond("s1", [], "?")
    assert "erro" in reply.tool_trace[0].result


def test_stops_runaway_tool_loops(make_agent):
    loop = LLMResponse(tool_calls=[ToolCall("get_store_policy", {"topic": "hours"})])
    agent, _ = make_agent([loop] * 10)
    reply = agent.respond("s1", [], "horário?")
    assert reply.text == FALLBACK_REPLY and reply.error


def test_provider_failure_returns_friendly_message(make_agent):
    agent, _ = make_agent([LLMError("quota")])
    reply = agent.respond("s1", [], "oi")
    assert reply.text == FALLBACK_REPLY and reply.error == "quota"


def test_rejects_oversized_messages_without_calling_the_model(make_agent):
    agent, provider = make_agent([])
    reply = agent.respond("s1", [], "a" * 5000)
    assert "longa" in reply.text and provider.system_prompt is None


def test_system_prompt_includes_reference_date():
    prompt = build_system_prompt(date(2026, 3, 25))
    assert "25/03/2026" in prompt and "quarta-feira" in prompt
