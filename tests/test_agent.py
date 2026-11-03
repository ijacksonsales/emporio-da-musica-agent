"""Agent loop tests with a scripted fake provider (no network)."""

from datetime import date

import pytest

from emporio_agent.agent import FALLBACK_REPLY, Agent, build_system_prompt
from emporio_agent.llm.base import LLMError, LLMResponse, Message, ToolCall
from emporio_agent.tools.handoff import HandoffStore


class ScriptedTurn:
    def __init__(self, responses):
        self.responses = list(responses)
        self.received = []

    def stream(self, tool_results=None):
        self.received.append(tool_results)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        for word in item.text.split(" ") if item.text else []:
            yield word + " "
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


def test_streams_text_and_returns_what_was_shown(make_agent):
    agent, _ = make_agent([
        LLMResponse(tool_calls=[ToolCall("get_store_policy", {"topic": "hours"})]),
        LLMResponse(text="Abrimos às 09:00 no sábado."),
    ])
    stream = agent.respond_stream("s1", [], "horário de sábado?")
    chunks = []
    while True:
        try:
            chunks.append(next(stream))
        except StopIteration as done:
            reply = done.value
            break
    assert len(chunks) > 1  # delivered word by word
    assert reply.text == "".join(chunks).strip()
    assert reply.tool_trace[0].call.name == "get_store_policy"


def test_failure_mid_stream_appends_fallback(make_agent):
    agent, _ = make_agent([
        LLMResponse(text="Deixa eu verificar.", tool_calls=[ToolCall("get_store_policy", {"topic": "hours"})]),
        LLMError("quota"),
    ])
    reply = agent.respond("s1", [], "horário?")
    assert reply.text.startswith("Deixa eu verificar.") and reply.text.endswith(FALLBACK_REPLY)
    assert reply.error == "quota"


def test_system_prompt_includes_reference_date():
    prompt = build_system_prompt(date(2026, 3, 25))
    assert "25/03/2026" in prompt and "quarta-feira" in prompt


def test_first_turn_asks_for_name_and_later_turns_do_not_welcome_again(make_agent):
    first = build_system_prompt(date(2026, 3, 25), first_turn=True)
    later = build_system_prompt(date(2026, 3, 25), first_turn=False)
    assert "first message" in first and "ask for it" in first
    assert "do not welcome the customer again" in later

    agent, provider = make_agent([LLMResponse(text="Oi!"), LLMResponse(text="Certo!")])
    agent.respond("s1", [], "Quanto custa o GD20?")
    assert "first message" in provider.system_prompt
    agent.respond("s1", [Message("user", "oi"), Message("assistant", "Oi! Qual seu nome?")], "Ana")
    assert "already under way" in provider.system_prompt
