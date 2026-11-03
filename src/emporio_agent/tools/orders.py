"""Order lookup with identity verification (decisions D10, D13)."""

from __future__ import annotations

import re
from datetime import date, timedelta

from emporio_agent.data.loader import Customer, Order, Store, digits
from emporio_agent.pricing import format_brl, money
from emporio_agent.tools import ToolError

MAX_FAILED_ATTEMPTS = 3

STATUS_LABELS = {
    "pending": "aguardando pagamento/processamento",
    "confirmed": "confirmado, em separação",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}

REGRET_DAYS = 7  # §4.1, from receipt
DEFECT_EXCHANGE_DAYS = 30  # §4.2, from purchase
LEGAL_WARRANTY_DAYS = 90  # §8.1, from receipt


class AttemptTracker:
    """Counts failed identity checks per conversation to block order-id enumeration."""

    def __init__(self) -> None:
        self._failures: dict[str, int] = {}

    def failures(self, session_id: str) -> int:
        return self._failures.get(session_id, 0)

    def register_failure(self, session_id: str) -> None:
        self._failures[session_id] = self.failures(session_id) + 1

    def locked(self, session_id: str) -> bool:
        return self.failures(session_id) >= MAX_FAILED_ATTEMPTS


def _payment_label(method: str) -> str:
    if m := re.fullmatch(r"credit_(\d+)x", method):
        return f"cartão de crédito em {m.group(1)}x"
    return {"pix": "PIX", "debit": "cartão de débito", "boleto": "boleto bancário"}.get(
        method, method
    )


def _contact_matches(customer: Customer, contact: str) -> bool:
    contact = contact.strip().lower()
    if "@" in contact:
        return contact == customer.email
    given = digits(contact)
    # compare the last 9 digits (mobile number without area/country code)
    return len(given) >= 9 and given[-9:] == digits(customer.phone)[-9:]


def _window(start: date | None, days: int, today: date) -> dict | None:
    if start is None:
        return None
    deadline = start + timedelta(days=days)
    return {
        "prazo_final": deadline.isoformat(),
        "dentro_do_prazo": today <= deadline,
        "dias_restantes": max((deadline - today).days, 0),
    }


def _describe(store: Store, order: Order, today: date) -> dict:
    customer = store.customers[order.customer_id]
    result = {
        "verificado": True,
        "cliente_primeiro_nome": customer.name.split()[0],
        "pedido": order.order_id,
        "data_pedido": order.order_date.isoformat(),
        "status": STATUS_LABELS.get(order.status, order.status),
        "itens": [
            {"produto": store.products[i.product_id].name, "quantidade": i.quantity}
            for i in order.items
        ],
        "total_registrado": format_brl(money(order.total)),
        "forma_pagamento": _payment_label(order.payment_method),
        "codigo_rastreio": order.tracking_code,
        "previsao_entrega": order.estimated_delivery.isoformat()
        if order.estimated_delivery
        else None,
        "data_referencia_hoje": today.isoformat(),
    }
    if order.notes:
        result["observacao_do_pedido"] = order.notes
    if order.status == "shipped" and order.estimated_delivery and today > order.estimated_delivery:
        result["atrasado"] = True
        result["dias_de_atraso"] = (today - order.estimated_delivery).days
    if order.status == "delivered":
        # Assumption F15: receipt date = estimated delivery date
        received = order.estimated_delivery
        result["prazos"] = {
            "arrependimento_7_dias_apos_recebimento": _window(received, REGRET_DAYS, today),
            "troca_por_defeito_30_dias_apos_compra": _window(
                order.order_date, DEFECT_EXCHANGE_DAYS, today
            ),
            "garantia_legal_90_dias_apos_recebimento": _window(
                received, LEGAL_WARRANTY_DAYS, today
            ),
            "premissa": "data de recebimento considerada igual à previsão de entrega",
        }
    if order.total_mismatch:
        result["observacao_interna"] = (
            "O total registrado difere da soma dos itens pelo preço atual. Não explique "
            "nem recalcule; se o cliente questionar o valor, encaminhe para a equipe."
        )
    return result


def get_order_status(
    store: Store,
    order_id: int | str,
    email_or_phone: str,
    today: date,
    attempts: AttemptTracker,
    session_id: str,
) -> dict:
    if attempts.locked(session_id):
        return {
            "verificado": False,
            "bloqueado": True,
            "observacao": (
                "Limite de tentativas de verificação atingido nesta conversa. Por segurança, "
                "encaminhe o cliente para a equipe humana."
            ),
        }

    order_text = str(order_id).strip().lstrip("#")
    if not order_text.isdigit() or len(order_text) > 9:
        raise ToolError("order_id deve ser o número do pedido")
    if not email_or_phone or len(email_or_phone) > 100:
        raise ToolError("informe o e-mail ou telefone cadastrado")

    order = store.orders.get(int(order_text))
    if order is None or not _contact_matches(store.customers[order.customer_id], email_or_phone):
        attempts.register_failure(session_id)
        # Same message for "order not found" and "wrong contact": no enumeration oracle.
        return {
            "verificado": False,
            "tentativas_restantes": MAX_FAILED_ATTEMPTS - attempts.failures(session_id),
            "observacao": (
                "Não foi possível confirmar o pedido com esses dados. Peça ao cliente para "
                "conferir o número do pedido e o e-mail ou telefone cadastrado."
            ),
        }

    return _describe(store, order, today)
