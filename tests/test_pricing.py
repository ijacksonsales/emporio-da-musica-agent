from decimal import Decimal

import pytest

from emporio_agent.data.loader import Promotion
from emporio_agent.pricing import format_brl, max_installments, quote


def test_pix_discount_applies_without_promotion():
    q = quote(1299)
    assert q.final_price == Decimal("1299.00")
    assert q.pix_price == Decimal("1234.05")


def test_promotion_is_not_cumulative_with_pix():
    # Product 90 (Crafter HT-100): R$ 2,399 with an active 18% promotion
    q = quote(2399, Promotion(90, 18, "Desconto Exclusivo"))
    assert q.final_price == Decimal("1967.18")
    assert q.pix_price == q.final_price


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (Decimal("40"), 1),  # below the R$ 50 minimum even in 2x
        (Decimal("159.90"), 3),  # 3x = 53.30; 4x would be below R$ 80
        (Decimal("349.90"), 4),  # 4x = 87.48; 5x = 69.98 < 80
        (Decimal("600"), 6),  # 6x = 100.00; 7x = 85.71 < 100
        (Decimal("1149"), 11),  # 11x = 104.45; 12x = 95.75 < 100
        (Decimal("7499"), 12),
    ],
)
def test_max_installments_respects_tier_minimums(amount, expected):
    assert max_installments(amount) == expected


def test_installment_value_and_combined_payment():
    q = quote(7499)
    assert q.max_installments == 12
    assert q.installment_value == Decimal("624.92")
    assert q.combined_payment_allowed
    assert not quote(1999).combined_payment_allowed


def test_format_brl():
    assert format_brl(Decimal("11499")) == "R$ 11.499,00"
    assert format_brl(Decimal("159.9")) == "R$ 159,90"
