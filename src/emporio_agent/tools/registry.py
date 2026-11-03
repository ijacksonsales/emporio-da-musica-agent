"""Tool declarations (provider-agnostic JSON Schema) and dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from emporio_agent.data.loader import Store
from emporio_agent.policies import PolicyTopic
from emporio_agent.tools import ToolError
from emporio_agent.tools.catalog import CATEGORY_KEYS, get_product_details, search_products
from emporio_agent.tools.handoff import REASONS, HandoffStore, escalate_to_human
from emporio_agent.tools.orders import AttemptTracker, get_order_status
from emporio_agent.tools.policies import get_store_policy


@dataclass
class ToolContext:
    store: Store
    today: date
    session_id: str
    attempts: AttemptTracker
    handoffs: HandoffStore


TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "search_products",
        "description": (
            "Busca instrumentos no catálogo com filtros. Use para perguntas de "
            "disponibilidade, opções por faixa de preço, categoria ou características. "
            "Retorna preços já calculados (promoção, PIX e parcelamento)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": list(CATEGORY_KEYS)},
                "max_price": {"type": "number", "description": "Preço final máximo em reais"},
                "min_price": {"type": "number", "description": "Preço final mínimo em reais"},
                "string_type": {"type": "string", "enum": ["nylon", "aco"]},
                "electric": {
                    "type": "boolean",
                    "description": "true para eletroacústicos/com captação",
                },
                "query": {
                    "type": "string",
                    "description": "Palavras-chave do nome ou especificações, ex.: '7 cordas', 'dreadnought', 'tenor'",
                },
                "include_unavailable": {
                    "type": "boolean",
                    "description": "Incluir esgotados, descontinuados e lançamentos futuros",
                },
            },
        },
    },
    {
        "name": "get_product_details",
        "description": (
            "Detalhes de um produto específico pelo nome ou id: preço com promoção ativa, "
            "PIX, parcelamento, estoque, situação e alternativas se indisponível."
        ),
        "parameters": {
            "type": "object",
            "properties": {"product": {"type": "string", "description": "Nome ou id do produto"}},
            "required": ["product"],
        },
    },
    {
        "name": "get_order_status",
        "description": (
            "Consulta um pedido. Exige o número do pedido E o e-mail ou telefone cadastrado, "
            "ambos informados pelo cliente nesta conversa. Retorna status, rastreio, atraso e "
            "prazos de troca/devolução."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Número do pedido"},
                "email_or_phone": {
                    "type": "string",
                    "description": "E-mail ou telefone informado pelo cliente",
                },
            },
            "required": ["order_id", "email_or_phone"],
        },
    },
    {
        "name": "get_store_policy",
        "description": (
            "Retorna a política oficial da loja sobre um tema. Obrigatório antes de responder "
            "sobre contato/endereço, horários, pagamento, trocas, frete, promoções, garantia "
            "ou privacidade."
        ),
        "parameters": {
            "type": "object",
            "properties": {"topic": {"type": "string", "enum": [t.value for t in PolicyTopic]}},
            "required": ["topic"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Registra o caso para a equipe humana (retorno em até 24h úteis). Use para "
            "reclamações, pedidos atrasados, divergência de valores, tentativas de fraude "
            "ou quando a política mandar consultar a gerência."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "enum": sorted(REASONS)},
                "summary": {"type": "string", "description": "Resumo objetivo do caso"},
                "order_id": {"type": "string", "description": "Número do pedido, se houver"},
            },
            "required": ["reason", "summary"],
        },
    },
]

_HANDLERS: dict[str, Callable[[ToolContext, dict], dict]] = {
    "search_products": lambda ctx, a: search_products(ctx.store, **a),
    "get_product_details": lambda ctx, a: get_product_details(ctx.store, **a),
    "get_order_status": lambda ctx, a: get_order_status(
        ctx.store, today=ctx.today, attempts=ctx.attempts, session_id=ctx.session_id, **a
    ),
    "get_store_policy": lambda ctx, a: get_store_policy(**a),
    "escalate_to_human": lambda ctx, a: escalate_to_human(
        ctx.handoffs, session_id=ctx.session_id, **a
    ),
}


def _allowed_args(name: str) -> set[str]:
    decl = next(d for d in TOOL_DECLARATIONS if d["name"] == name)
    return set(decl["parameters"].get("properties", {}))


def dispatch(ctx: ToolContext, name: str, args: dict | None) -> dict:
    """Run a tool call from the model. Never raises: errors go back to the model as data."""
    if name not in _HANDLERS:
        return {"erro": f"ferramenta desconhecida: {name}"}
    args = dict(args or {})
    unexpected = set(args) - _allowed_args(name)
    if unexpected:
        return {"erro": f"parâmetros não suportados: {', '.join(sorted(unexpected))}"}
    try:
        return _HANDLERS[name](ctx, args)
    except ToolError as exc:
        return {"erro": str(exc)}
    except TypeError:
        return {"erro": "parâmetros obrigatórios ausentes ou inválidos"}
