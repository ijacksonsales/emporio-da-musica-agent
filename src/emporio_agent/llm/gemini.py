"""Gemini implementation of the provider interface, using the official google-genai SDK."""

from __future__ import annotations

import time
from typing import Any

from google import genai
from google.genai import errors, types

from emporio_agent.llm.base import ChatTurn, LLMError, LLMResponse, Message, ToolCall, ToolResult

RETRYABLE_STATUS = {429, 500, 503}
MAX_RETRIES = 3


class GeminiTurn(ChatTurn):
    def __init__(
        self,
        client: genai.Client,
        model: str,
        config: types.GenerateContentConfig,
        contents: list[types.Content],
    ) -> None:
        self._client = client
        self._model = model
        self._config = config
        self._contents = contents

    def _generate(self) -> types.GenerateContentResponse:
        for attempt in range(MAX_RETRIES):
            try:
                return self._client.models.generate_content(
                    model=self._model, contents=self._contents, config=self._config
                )
            except errors.APIError as exc:
                if exc.code in RETRYABLE_STATUS and attempt < MAX_RETRIES - 1:
                    time.sleep(2**attempt * 2)
                    continue
                if exc.code == 429:
                    raise LLMError("Limite de uso do modelo atingido (free tier).") from exc
                raise LLMError(f"Falha ao chamar o modelo (HTTP {exc.code}).") from exc
        raise LLMError("Falha ao chamar o modelo.")  # pragma: no cover

    def next(self, tool_results: list[ToolResult] | None = None) -> LLMResponse:
        if tool_results:
            self._contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(name=r.call.name, response=r.result)
                        for r in tool_results
                    ],
                )
            )

        response = self._generate()
        candidate = response.candidates[0] if response.candidates else None
        if candidate is None or candidate.content is None:
            return LLMResponse(text="")

        # Keep the model turn as returned (including thought signatures) for the next call.
        self._contents.append(candidate.content)
        parts = candidate.content.parts or []
        calls = [
            ToolCall(name=p.function_call.name, args=dict(p.function_call.args or {}), id=p.function_call.id)
            for p in parts
            if p.function_call
        ]
        text = "".join(p.text for p in parts if p.text and not p.thought)
        return LLMResponse(text=text.strip(), tool_calls=calls)


class GeminiProvider:
    def __init__(self, api_key: str | None, model: str, temperature: float = 0.3) -> None:
        if not api_key:
            raise LLMError("GEMINI_API_KEY não configurada. Veja o README.")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._temperature = temperature

    def begin_turn(
        self,
        system_prompt: str,
        history: list[Message],
        user_message: str,
        tools: list[dict[str, Any]],
    ) -> GeminiTurn:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self._temperature,
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=t["name"],
                            description=t["description"],
                            parameters_json_schema=t["parameters"],
                        )
                        for t in tools
                    ]
                )
            ],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        contents = [
            types.Content(
                role="model" if m.role == "assistant" else "user",
                parts=[types.Part.from_text(text=m.text)],
            )
            for m in history
        ]
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))
        return GeminiTurn(self._client, self._model, config, contents)
