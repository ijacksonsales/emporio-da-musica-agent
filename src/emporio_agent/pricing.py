"""Price rules from the policy manual, computed in code (decision D09).

- Active promotion: final price = list price - discount %.
- PIX: 5% off the list price, only when no promotion applies (not cumulative, §6.2).
- Credit card: up to 12x interest-free, with a minimum installment per tier (§3.1).
- Combined payment methods allowed above R$ 2,000 (§3.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from emporio_agent.data.loader import Promotion

PIX_DISCOUNT = Decimal("0.05")
COMBINED_PAYMENT_THRESHOLD = Decimal("2000")
MAX_INSTALLMENTS = 12


def money(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_brl(value: Decimal) -> str:
    """Decimal(1299.9) -> 'R$ 1.299,90'."""
    whole, cents = f"{value:,.2f}".split(".")
    return f"R$ {whole.replace(',', '.')},{cents}"


def min_installment(n: int) -> Decimal:
    if n <= 3:
        return Decimal("50")
    if n <= 6:
        return Decimal("80")
    return Decimal("100")


def max_installments(amount: Decimal) -> int:
    """Largest number of installments whose value respects the tier minimum."""
    valid = [n for n in range(2, MAX_INSTALLMENTS + 1) if amount / n >= min_installment(n)]
    return max(valid, default=1)


@dataclass(frozen=True)
class PriceQuote:
    list_price: Decimal
    final_price: Decimal
    promotion: Promotion | None
    pix_price: Decimal
    max_installments: int
    installment_value: Decimal
    combined_payment_allowed: bool

    def to_dict(self) -> dict:
        data = {
            "preco_tabela": format_brl(self.list_price),
            "preco_final": format_brl(self.final_price),
            "pix": format_brl(self.pix_price),
            "cartao_credito": (
                f"até {self.max_installments}x sem juros de {format_brl(self.installment_value)}"
                if self.max_installments > 1
                else "somente à vista (valor abaixo da parcela mínima)"
            ),
            "permite_combinar_formas_de_pagamento": self.combined_payment_allowed,
        }
        if self.promotion:
            data["promocao_ativa"] = {
                "nome": self.promotion.description,
                "desconto": f"{self.promotion.discount_percent}%",
                "observacao": "preço promocional; desconto de PIX não é cumulativo",
            }
        else:
            data["promocao_ativa"] = None
        return data


def quote(list_price: float, promotion: Promotion | None = None) -> PriceQuote:
    base = money(list_price)
    if promotion:
        final = money(base * (1 - Decimal(promotion.discount_percent) / 100))
        pix = final  # not cumulative
    else:
        final = base
        pix = money(base * (1 - PIX_DISCOUNT))
    n = max_installments(final)
    return PriceQuote(
        list_price=base,
        final_price=final,
        promotion=promotion,
        pix_price=pix,
        max_installments=n,
        installment_value=money(final / n),
        combined_payment_allowed=final > COMBINED_PAYMENT_THRESHOLD,
    )
