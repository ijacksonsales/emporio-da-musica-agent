"""Gemini implementation of the provider interface, using the official google-genai SDK."""

from __future__ import annotations

import time
from collections.abc import Generator, Iterator
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
        fallback_model: str | None = None,
    ) -> None:
        self._client = client
        self.model = model  # model actually answering; changes if the fallback kicks in
        self._fallback_model = fallback_model
        self._config = config
        self._contents = contents

    def _switch_to_fallback(self) -> bool:
        if not self._fallback_model or self.model == self._fallback_model:
            return False
        self.model = self._fallback_model
        return True

    def _chunks(self) -> Iterator[types.GenerateContentResponse]:
        """Stream response chunks, retrying transient errors only before the first chunk.

        On a quota error (429) the turn switches to the fallback model right away (D26):
        waiting does not help when a daily quota is exhausted, and the fallback has its
        own quota.
        """
        attempt = 0
        while True:
            started = False
            try:
                for chunk in self._client.models.generate_content_stream(
                    model=self.model, contents=self._contents, config=self._config
                ):
                    started = True
                    yield chunk
                return
            except errors.APIError as exc:
                if not started and exc.code == 429 and self._switch_to_fallback():
                    continue
                attempt += 1
                if not started and exc.code in RETRYABLE_STATUS and attempt < MAX_RETRIES:
                    time.sleep(2 ** (attempt - 1) * 2)
                    continue
                if exc.code == 429:
                    raise LLMError("Limite de uso do modelo atingido (free tier).") from exc
                raise LLMError(f"Falha ao chamar o modelo (HTTP {exc.code}).") from exc

    def stream(
        self, tool_results: list[ToolResult] | None = None, correction: str | None = None
    ) -> Generator[str, None, LLMResponse]:
        if correction:
            self._contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=correction)])
            )
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

        parts: list[types.Part] = []
        calls: list[ToolCall] = []
        text: list[str] = []
        for chunk in self._chunks():
            candidate = chunk.candidates[0] if chunk.candidates else None
            if candidate is None or candidate.content is None:
                continue
            for part in candidate.content.parts or []:
                parts.append(part)
                if part.function_call:
                    fc = part.function_call
                    calls.append(ToolCall(name=fc.name, args=dict(fc.args or {}), id=fc.id))
                elif part.text and not part.thought:
                    text.append(part.text)
                    yield part.text

        # Keep the model turn as returned (including thought signatures) for the next call.
        if parts:
            self._contents.append(types.Content(role="model", parts=parts))
        return LLMResponse(text="".join(text).strip(), tool_calls=calls)


class GeminiProvider:
    def __init__(
        self,
        api_key: str | None,
        model: str,
        fallback_model: str | None = None,
        temperature: float = 0.3,
    ) -> None:
        if not api_key:
            raise LLMError("GEMINI_API_KEY não configurada. Veja o README.")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._fallback_model = fallback_model or None
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
        return GeminiTurn(self._client, self._model, config, contents, self._fallback_model)
