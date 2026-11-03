"""Agent loop: send the user message, execute requested tools, repeat until a text reply."""

from __future__ import annotations

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


def build_system_prompt(today: date, now: datetime | None = None) -> str:
    now = now or datetime.now(STORE_TZ)
    template = (resources.files("emporio_agent") / "prompts" / "system_prompt.md").read_text(
        encoding="utf-8"
    )
    return template.format(
        today=today.strftime("%d/%m/%Y"),
        today_weekday=WEEKDAYS[today.weekday()],
        now_time=now.strftime("%H:%M"),
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
        user_message = user_message.strip()
        if not user_message:
            return AgentReply(text="Oi! Como posso te ajudar?")
        if len(user_message) > MAX_USER_MESSAGE_LENGTH:
            return AgentReply(
                text="Sua mensagem ficou bem longa! Pode resumir em poucas linhas o que você precisa?"
            )

        ctx = ToolContext(self.store, self.today, session_id, self.attempts, self.handoffs)
        trace: list[ToolResult] = []
        try:
            turn = self.provider.begin_turn(
                build_system_prompt(self.today), history, user_message, TOOL_DECLARATIONS
            )
            response = turn.next()
            for _ in range(MAX_TOOL_ROUNDS):
                if not response.tool_calls:
                    break
                results = [self._run(ctx, call) for call in response.tool_calls]
                trace.extend(results)
                response = turn.next(results)
            else:
                return AgentReply(text=FALLBACK_REPLY, tool_trace=trace, error="too many tool rounds")
        except LLMError as exc:
            return AgentReply(text=FALLBACK_REPLY, tool_trace=trace, error=str(exc))

        return AgentReply(text=response.text or FALLBACK_REPLY, tool_trace=trace)

    @staticmethod
    def _run(ctx: ToolContext, call: ToolCall) -> ToolResult:
        return ToolResult(call=call, result=dispatch(ctx, call.name, call.args))
