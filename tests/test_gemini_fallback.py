"""Fallback model on quota errors (D26), with a fake Gemini client (no network)."""

from types import SimpleNamespace

import pytest
from google.genai import errors, types

from emporio_agent.llm.base import LLMError
from emporio_agent.llm.gemini import GeminiTurn

QUOTA = {"error": {"code": 429, "message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}}


def text_chunk(text):
    content = types.Content(role="model", parts=[types.Part.from_text(text=text)])
    return types.GenerateContentResponse(candidates=[types.Candidate(content=content)])


class FakeModels:
    def __init__(self, exhausted):
        self.exhausted = set(exhausted)
        self.calls = []

    def generate_content_stream(self, model, contents, config):
        self.calls.append(model)
        if model in self.exhausted:
            raise errors.APIError(429, QUOTA)
        yield text_chunk(f"resposta do {model}")


def make_turn(exhausted, fallback="fallback-model"):
    client = SimpleNamespace(models=FakeModels(exhausted))
    turn = GeminiTurn(client, "main-model", types.GenerateContentConfig(), [], fallback)
    return turn, client.models


def run(turn):
    stream = turn.stream()
    while True:
        try:
            next(stream)
        except StopIteration as done:
            return done.value


def test_uses_main_model_when_available():
    turn, models = make_turn(exhausted=[])
    assert run(turn).text == "resposta do main-model"
    assert models.calls == ["main-model"]


def test_switches_to_fallback_immediately_on_quota_error(monkeypatch):
    monkeypatch.setattr("emporio_agent.llm.gemini.time.sleep", lambda s: pytest.fail("should not wait"))
    turn, models = make_turn(exhausted=["main-model"])
    assert run(turn).text == "resposta do fallback-model"
    assert turn.model == "fallback-model"
    assert models.calls == ["main-model", "fallback-model"]


def test_raises_friendly_error_when_both_models_are_exhausted(monkeypatch):
    monkeypatch.setattr("emporio_agent.llm.gemini.time.sleep", lambda s: None)
    turn, _ = make_turn(exhausted=["main-model", "fallback-model"])
    with pytest.raises(LLMError, match="Limite de uso"):
        run(turn)


def test_no_fallback_configured(monkeypatch):
    monkeypatch.setattr("emporio_agent.llm.gemini.time.sleep", lambda s: None)
    turn, models = make_turn(exhausted=["main-model"], fallback=None)
    with pytest.raises(LLMError):
        run(turn)
    assert set(models.calls) == {"main-model"}
