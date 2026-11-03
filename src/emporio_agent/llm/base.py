"""Provider-agnostic interface for chat models with function calling (decision D04).

The agent loop only talks to these types, so swapping Gemini for another provider
means adding one module that implements `LLMProvider`.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass
class Message:
    role: Literal["user", "assistant"]
    text: str


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]
    id: str | None = None


@dataclass
class ToolResult:
    call: ToolCall
    result: dict[str, Any]


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMError(RuntimeError):
    """Provider failure (quota, network, invalid key). Message is safe to show to users."""


class ChatTurn(Protocol):
    """One user turn. The provider keeps the in-turn transcript (model calls, tool results).

    `stream` yields text chunks as the model generates them and returns the complete
    LLMResponse (text + tool calls) as the generator's return value. `correction` adds an
    internal note from the agent (e.g. a failed grounding check) before generating.
    """

    def stream(
        self, tool_results: list[ToolResult] | None = None, correction: str | None = None
    ) -> Generator[str, None, LLMResponse]: ...


class LLMProvider(Protocol):
    def begin_turn(
        self,
        system_prompt: str,
        history: list[Message],
        user_message: str,
        tools: list[dict[str, Any]],
    ) -> ChatTurn: ...
