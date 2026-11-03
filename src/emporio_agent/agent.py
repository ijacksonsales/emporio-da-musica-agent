"""Agent loop: send the user message, execute requested tools, repeat until a text reply."""

from __future__ import annotations

import re
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

# Tools whose results can back a price or order fact (D23).
GROUNDING_TOOLS = {"search_products", "get_product_details", "get_order_status"}
PRICE_PATTERN = re.compile(r"R\$\s?\d")
PROMISE_PATTERN = re.compile(
    r"\b(vou verificar|vou consultar|vou checar|vou conferir|deixa eu (ver|verificar|consultar)"
    r"|só um (instante|momento)|um momento)\b",
    re.IGNORECASE,
)
_CORRECTION_PREFIX = (
    "[Verificação interna do sistema, não é mensagem do cliente] Sua resposta anterior NÃO "
    "foi mostrada ao cliente. "
)
GROUNDING_CORRECTIONS = {
    "price": _CORRECTION_PREFIX
    + "Ela citou preços sem consultar nenhuma ferramenta neste turno. Preços e produtos só "
    "podem vir das ferramentas. Chame a ferramenta adequada agora e responda de novo ao "
    "cliente com base no resultado.",
    "promise": _CORRECTION_PREFIX
    + "Ela prometeu verificar algo, mas não chamou nenhuma ferramenta. Chame agora a "
    "ferramenta necessária e responda ao cliente com a informação, sem notas sobre você.",
    "welcome": _CORRECTION_PREFIX
    + "É a primeira mensagem da conversa e ela não começou com as boas-vindas. Reescreva "
    "começando com \"Oi! Boas-vindas à Empório da Música! Eu sou a Lia\" e siga as "
    "instruções de abertura (pergunte o nome se o cliente ainda não disse).",
}

FALLBACK_REPLY = (
    "Desculpa, tive um problema técnico agora e não consegui concluir sua solicitação. "
    "Pode tentar de novo em instantes? Se preferir, fale com a equipe pelo WhatsApp (67) 3321-4500."
)


@dataclass
class AgentReply:
    text: str
    tool_trace: list[ToolResult] = field(default_factory=list)
    error: str | None = None
    model: str | None = None  # model that produced the reply (differs if the fallback was used)


FIRST_TURN_STAGE = (
    "This is the **first message** of the conversation. Did the customer say their name in it?\n"
    "- **NO name** → your whole reply is ONLY the welcome and the name question, nothing "
    "else: no tools, no product or policy information, no requests for order data. Use this "
    "template, adapting only the middle sentence to what they asked:\n"
    "  \"Oi! Boas-vindas à Empório da Música! 🎸 Eu sou a Lia, assistente virtual da loja. "
    "Já te ajudo com [assunto]! Antes, como posso te chamar?\"\n"
    "- **Name given** → start with \"Oi, [nome]! Boas-vindas à Empório da Música! Eu sou a "
    "Lia.\" and then fully answer their question in this same message, calling the tools "
    "you need."
)
ONGOING_STAGE = (
    "The conversation is already under way: do not welcome the customer again.\n"
    "- If you had asked for the name and the customer gave it, greet them by name and now "
    "answer what they asked in their first message (look back at the history).\n"
    "- If they declined or ignored the name question, say something like \"Sem problemas!\" "
    "and go straight to helping, without using any name."
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

        def grounded() -> bool:
            return any(t.call.name in GROUNDING_TOOLS for t in trace)

        try:
            turn = self.provider.begin_turn(
                build_system_prompt(self.today, first_turn=not history),
                history,
                user_message,
                TOOL_DECLARATIONS,
            )
            results: list[ToolResult] | None = None
            correction: str | None = None
            corrected = False
            for _ in range(MAX_TOOL_ROUNDS + 2):
                if shown and results:
                    yield emit("\n\n")  # separate text written before and after tool calls
                stream = turn.stream(results, correction)
                correction = None
                # Grounding guard: until a data tool has run in this turn, hold the text back
                # so a reply quoting prices from nowhere can be rejected before it is shown.
                live = grounded()
                held: list[str] = []
                while True:
                    try:
                        chunk = next(stream)
                    except StopIteration as done:
                        response = done.value
                        break
                    if live:
                        yield emit(chunk)
                    else:
                        held.append(chunk)

                text = "".join(held)
                violation = None
                if held and PRICE_PATTERN.search(text):
                    violation = "price"
                elif held and not response.tool_calls and PROMISE_PATTERN.search(text):
                    violation = "promise"  # said it would check, then stopped
                elif (
                    not history and not trace and held and not response.tool_calls
                    and "boas-vindas" not in text.lower()
                ):
                    violation = "welcome"  # first message must open with the welcome (D21)
                if violation:
                    if response.tool_calls:
                        held = []  # drop the ungrounded preamble; the tools will ground the answer
                    elif not corrected:
                        corrected = True
                        correction = GROUNDING_CORRECTIONS[violation]
                        results = None
                        continue
                    else:
                        return (yield from fail(f"grounding check failed twice ({violation})"))
                if held:
                    yield emit(text)

                if not response.tool_calls:
                    break
                results = [self._run(ctx, call) for call in response.tool_calls]
                trace.extend(results)
            else:
                return (yield from fail("too many tool rounds"))
        except LLMError as exc:
            return (yield from fail(str(exc)))

        final = re.sub(r"\n{3,}", "\n\n", "".join(shown)).strip()
        if not final:
            return (yield from fail("empty response"))
        return AgentReply(text=final, tool_trace=trace, model=getattr(turn, "model", None))

    @staticmethod
    def _run(ctx: ToolContext, call: ToolCall) -> ToolResult:
        return ToolResult(call=call, result=dispatch(ctx, call.name, call.args))
