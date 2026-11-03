"""Agent loop: send the user message, execute requested tools, repeat until a text reply."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib import resources
from zoneinfo import ZoneInfo

from emporio_agent.data.loader import Store
from emporio_agent.llm.base import LLMError, LLMProvider, Message, ToolCall, ToolResult
from emporio_agent.tools.handoff import HandoffStore
from emporio_agent.tools.orders import AttemptTracker
from emporio_agent.tools.registry import TOOL_DECLARATIONS, ToolContext, dispatch

MAX_TOOL_ROUNDS = 6
MAX_USER_MESSAGE_LENGTH = 2000
STORE_TZ = ZoneInfo("America/Campo_Grande")
WEEKDAYS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

FALLBACK_REPLY = (
    "Desculpa, tive um problema técnico agora e não consegui concluir sua solicitação. "
    "Pode tentar de novo em instantes? Se preferir, fale com a equipe pelo WhatsApp (67) 3321-4500."
)


@dataclass
class AgentReply:
    text: str
    tool_trace: list[ToolResult] = field(default_factory=list)
    error: str | None = None


FIRST_TURN_STAGE = (
    "This is the **first message** of the conversation. Start with a warm welcome to "
    "Empório da Música and introduce yourself as Lia. Then follow exactly one case:\n"
    "- **Case A: the customer did NOT say their name.** Ask for it before answering. If they "
    "already asked something, acknowledge it (e.g. \"já te ajudo com isso!\") so they don't "
    "feel ignored. In this case only, do not call tools and do not answer yet.\n"
    "- **Case B: the customer said their name.** Do not ask for it. Welcome them by name AND "
    "fully answer their question in this same message, calling the tools you need."
)
ONGOING_STAGE = (
    "- The conversation is already under way: do not welcome the customer again.\n"
    "- If you asked for the name and the customer gave it, use it from now on and answer "
    "what they had asked. If they declined or ignored the question, do not insist: go "
    "straight to helping."
)


def build_system_prompt(today: date, first_turn: bool = False, now: datetime | None = None) -> str:
    now = now or datetime.now(STORE_TZ)
    template = (resources.files("emporio_agent") / "prompts" / "system_prompt.md").read_text(
        encoding="utf-8"
    )
    return template.format(
        today=today.strftime("%d/%m/%Y"),
        today_weekday=WEEKDAYS[today.weekday()],
        now_time=now.strftime("%H:%M"),
        conversation_stage=FIRST_TURN_STAGE if first_turn else ONGOING_STAGE,
    )


class Agent:
    def __init__(
        self,
        provider: LLMProvider,
        store: Store,
        today: date,
        handoffs: HandoffStore,
        attempts: AttemptTracker | None = None,
    ) -> None:
        self.provider = provider
        self.store = store
        self.today = today
        self.handoffs = handoffs
        self.attempts = attempts or AttemptTracker()

    def respond(self, session_id: str, history: list[Message], user_message: str) -> AgentReply:
        """Non-streaming variant: consume the stream and return the final reply."""
        stream = self.respond_stream(session_id, history, user_message)
        while True:
            try:
                next(stream)
            except StopIteration as done:
                return done.value

    def respond_stream(
        self, session_id: str, history: list[Message], user_message: str
    ) -> Generator[str, None, AgentReply]:
        """Yield reply text as it is generated; return the final AgentReply.

        The returned text is exactly what was yielded, so what the customer saw is
        what gets stored in the history.
        """
        user_message = user_message.strip()
        if not user_message:
            text = "Oi! Como posso te ajudar?"
            yield text
            return AgentReply(text=text)
        if len(user_message) > MAX_USER_MESSAGE_LENGTH:
            text = "Sua mensagem ficou bem longa! Pode resumir em poucas linhas o que você precisa?"
            yield text
            return AgentReply(text=text)

        ctx = ToolContext(self.store, self.today, session_id, self.attempts, self.handoffs)
        trace: list[ToolResult] = []
        shown: list[str] = []

        def emit(chunk: str) -> str:
            shown.append(chunk)
            return chunk

        def fail(error: str) -> Generator[str, None, AgentReply]:
            yield emit(("\n\n" if shown else "") + FALLBACK_REPLY)
            return AgentReply(text="".join(shown), tool_trace=trace, error=error)

        try:
            turn = self.provider.begin_turn(
                build_system_prompt(self.today, first_turn=not history),
                history,
                user_message,
                TOOL_DECLARATIONS,
            )
            results: list[ToolResult] | None = None
            for _ in range(MAX_TOOL_ROUNDS + 1):
                if shown and results:
                    yield emit("\n\n")  # separate text written before and after tool calls
                stream = turn.stream(results)
                while True:
                    try:
                        yield emit(next(stream))
                    except StopIteration as done:
                        response = done.value
                        break
                if not response.tool_calls:
                    break
                results = [self._run(ctx, call) for call in response.tool_calls]
                trace.extend(results)
            else:
                return (yield from fail("too many tool rounds"))
        except LLMError as exc:
            return (yield from fail(str(exc)))

        if not "".join(shown).strip():
            return (yield from fail("empty response"))
        return AgentReply(text="".join(shown).strip(), tool_trace=trace)

    @staticmethod
    def _run(ctx: ToolContext, call: ToolCall) -> ToolResult:
        return ToolResult(call=call, result=dispatch(ctx, call.name, call.args))
